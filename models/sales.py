from odoo import fields, models, api, _
from odoo.exceptions import UserError


class farm_sales(models.Model):
    _name = 'farm.sales'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'sales order'
    _order = 'issue_date'

    name = fields.Char(
        string = 'Sales Ref',
        index = True,
        readonly = True,
        tracking = True,
        default = lambda x: _('New'))
    state = fields.Selection([
        ('order', 'Invoicing'),
        ('lock', 'Locked')],
        string = 'State', readonly = False, copy = False,
        tracking = True, default = 'order')
    category_id = fields.Many2one(
        'product.category',
        required = True,
        domain = [('order_type', '=', 'sales')],
        string = 'Product Category')
    projects_id = fields.Many2one(
        'farm.projects',
        required = True,
        tracking = True)
    short_name = fields.Char(
        related = 'projects_id.short_name',
        store = True)
    issue_date = fields.Date(
        string = 'Date',
        default = fields.Datetime.today,
        tracking = True)
    partner_id = fields.Many2one(
        'res.partner',
        required = True,
        string = 'Partner')
    payment_term_id = fields.Many2one(
        'account.payment.term',
        'Payment Terms',
        domain = "['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    stock_warehouse = fields.Many2one(
        'stock.warehouse',
        string = 'Warehouse')
    s_order_cost = fields.Float(
        string = 'Order Cost',
        compute = '_compute_sales_order_cost',
        store = True)
    active = fields.Boolean(
        string = "Active",
        default = True,
        tracking = True)
    user_id = fields.Many2one(
        'res.users',
        string = "Order Man",
        required = True)
    notes = fields.Html(
        'Terms and Conditions')
    sales_order_line_ids = fields.One2many(
        'farm.sales.oline',
        'sales_id',
        string = "order lines")
    notes = fields.Html(
        'Terms and Conditions')
    company_id = fields.Many2one(
        'res.company',
        string = 'Company',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True)
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        related = 'company_id.currency_id',
        readonly = True,
        ondelete = 'set null',
        help = "Used to display the currency when tracking monetary values")
    customer_invoice_count = fields.Integer(
        string = "Customer Invoice Count",
        compute = '_compute_customer_invoice_count')
    customer_invoice_total = fields.Integer(
        string = "Customer Invoice Total",
        compute = '_compute_customer_invoice_total')
    analytic_account_id = fields.Reference(
        related = 'projects_id.analytic_account_id')

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('sales_order_line_ids')
    def _compute_sales_order_cost(self):
        for rec in self:
            sline = sum(self.env['farm.sales.oline'].search([('sales_id', '=', rec.id)]).mapped('price_subtotal'))
            rec.s_order_cost = sline
        return rec.s_order_cost

    def _compute_customer_invoice_count(self):
        for rec in self:
            customer_invoice_count = self.env['account.move'].search_count([('invoice_origin', '=', rec.name)])
            rec.customer_invoice_count = customer_invoice_count

    def _compute_customer_invoice_total(self):
        for rec in self:
            total = sum(
                self.env['account.move'].search([('invoice_origin', '=', rec.name)]).mapped('amount_total_signed'))
            rec.customer_invoice_total = total
        return rec.customer_invoice_total

    # -------------------------------------------------------------------------
    # Create METHODS
    # -------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('farm.sales') or _('New')
        return super(farm_sales, self).create(vals)

    def action_customer_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Invoices',
            'res_model': 'account.move',
            'domain': [('invoice_origin', '=', self.name)],
            'view_mode': 'tree',
            'context': {},
            'target': 'new'
        }

    def button_farm_customer_invoice(self):
        # create Customer Invoice in background and open form view.
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'out_invoice')
        journal = self.env['account.move'].with_context(
            default_move_type = move_type)._get_default_journal()
        if not journal:
            raise UserError(
                _('Please define an accounting sales journal for the company %s (%s).', self.company_id.name,
                  self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
        partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(
            ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]
        invoice_vals = {
            'state': 'draft',
            'ref': self.name or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
            'partner_id': partner_invoice_id,
            # 'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.name or '',
            'partner_bank_id': partner_bank_id.id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [(0, 0, {
                'sequence': self.sales_order_line_ids.sequence,
                'product_id': self.sales_order_line_ids.product_id.id,
                'product_uom_id': self.sales_order_line_ids.product_uom.id,
                'quantity': self.sales_order_line_ids.qty,
                'price_unit': self.sales_order_line_ids.price_unit,
                'analytic_account_id': self.analytic_account_id.id,
            })],
            'company_id': self.company_id.id,
        }
        invoice = self.env['account.move'].create(invoice_vals)
        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
        res = self.env.ref('account.view_move_form', False)
        form_view = [(res and res.id or False, 'form')]
        result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
        result['res_id'] = invoice.id
        return result


class farm_sales_oline(models.Model):
    _name = 'farm.sales.oline'
    _description = 'sales order'

    name = fields.Text(
        string = 'Description',
        required = True)
    sequence = fields.Integer(
        string = 'Sequence',
        default = 10)
    product_id = fields.Many2one(
        'product.product',
        required = True,
        domain = "[('categ_id', '=', categ_id)]")
    categ_id = fields.Many2one(
        related = 'sales_id.category_id',
        string = 'Category')
    price_unit = fields.Float(
        string = 'Price')
    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related = 'product_id.uom_id',
        domain = "[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float('Quantity')
    company_id = fields.Many2one(
        'res.company',
        string = 'Company',
        related = 'sales_id.company_id',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True)
    currency_id = fields.Many2one(
        'res.currency',
        string = 'Currency',
        related = 'sales_id.currency_id',
        readonly = True,
        help = "Used to display the currency when tracking monetary values")
    note = fields.Char(
        'Short Note')
    price_subtotal = fields.Monetary(
        string = 'Subtotal',
        compute = '_compute_subtotal',
        currency_field = 'currency_id',
        store = True)
    sales_id = fields.Many2one(
        'farm.sales',
        string = 'Sales Order')

    @api.onchange('product_id')
    def onchange_price_unit(self):
        if not self.product_id:
            self.price_unit = 0
            return
        self.price_unit = self.product_id.list_price

    @api.depends('price_unit', 'qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.qty
