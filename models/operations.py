from odoo import fields, models, api, _
from odoo.exceptions import UserError


class FarmOperations(models.Model):
    _name = 'farm.operations'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Operation Orders'
    _check_company_auto = True
    _order = 'issue_date'

    name = fields.Char(
        string='Operation Ref',
        index=True,
        readonly=True,
        tracking=True,
        default=lambda x: _('New'))
    state = fields.Selection([
        ('order', 'Invoicing'),
        ('lock', 'Locked')],
        default='order',
        string='Status',
        readonly=False,
        index=True,
        copy=False,
        tracking=True)
    category_id = fields.Many2one(
        comodel_name='product.category',
        required=True,
        domain=[('order_type', '=', 'service')],
        string='Product Category')
    projects_id = fields.Many2one(
        comodel_name='farm.projects',
        required=True,
        tracking=True)
    short_name = fields.Char(
        related='projects_id.short_name',
        store=True)
    issue_date = fields.Date(
        string='Date',
        default=fields.Datetime.today,
        tracking=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        string='Partner')
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Payment Terms',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    stock_warehouse = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse')
    o_order_cost = fields.Monetary(
        string='Order Cost',
        compute='_compute_operation_order_cost',
        currency_field='currency_id',
        store=True)
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Order Man",
        required=True)
    notes = fields.Html(
        string='Terms and Conditions')
    operation_order_line_ids = fields.One2many(
        comodel_name='farm.operations.oline',
        inverse_name='operations_id',
        string="order lines")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        change_default=True,
        default=lambda self: self.env.company,
        required=False,
        readonly=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
        ondelete='set null',
        help="Used to display the currency when tracking monetary values")
    vendor_bill_count = fields.Integer(
        string="Vendor Bill Count",
        compute='_compute_vendor_bill_count')
    vendor_bill_total = fields.Integer(
        string="Vendor Bill Total",
        compute='_compute_vendor_bill_total')
    invoice_count = fields.Integer(
        compute="_compute_invoice",
        string='Bill Count',
        copy=False,
        default=0,
        store=True)
    invoice_ids = fields.Many2many(
        'account.move',
        compute="_compute_invoice",
        string='Bills',
        copy=False,
        store=True)
    analytic_account_id = fields.Reference(
        related='projects_id.analytic_account_id')

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('operation_order_line_ids')
    def _compute_operation_order_cost(self):
        for rec in self:
            oline = sum(
                self.env['farm.operations.oline'].search(
                    [('operations_id', '=', rec.id)]).mapped('price_subtotal'))
            rec.o_order_cost = oline
        return rec.o_order_cost

    def _compute_vendor_bill_count(self):
        for rec in self:
            vendor_bill_count = self.env['account.move'].search_count([
                ('invoice_origin', '=', rec.name)
            ])
            rec.vendor_bill_count = vendor_bill_count

    def _compute_vendor_bill_total(self):
        for rec in self:
            total_debit = sum(
                self.env['account.move.line'].search([
                    ('operations_id', '=', rec.id)
                ]).mapped('debit')
            )
            total_credit = sum(
                self.env['account.move.line'].search([
                    ('operations_id', '=', rec.id)
                ]).mapped('credit')
            )
            rec.vendor_bill_total = total_debit - total_credit
        return rec.vendor_bill_total

    # compute invoice without link to views
    @api.depends('operation_order_line_ids.invoice_lines.move_id')
    def _compute_invoice(self):
        for order in self:
            invoices = order.mapped(
                'operation_order_line_ids.invoice_lines.move_id')
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    # -------------------------------------------------------------------------
    # Create METHODS
    # -------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'farm.operations') or _('New')
        return super(FarmOperations, self).create(vals)

    def action_vendor_bill(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bills',
            'res_model': 'account.move',
            'domain': [('invoice_origin', '=', self.name)],
            'view_mode': 'tree,form',
            'context': {},
            'target': 'current'
        }

    def button_farm_create_vendor_bill(self):
        # create vendor bill in background and open form view.
        self.ensure_one()

        # check analytic_account_id created
        analytic = self.analytic_account_id
        if not analytic:
            raise UserError(
                _('Please define an analytic account for the company %s (%s).') % (
                    self.company_id.name, self.company_id.id))

        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(
            default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(
                _('Please define an accounting purchase journal for the company %s (%s).') % (
                    self.company_id.name, self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'])[
            'invoice']
        partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(
            ['|', ('company_id', '=', False),
             ('company_id', '=', self.company_id.id)])[:1]
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
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [(0, 0, {
                'sequence': self.operation_order_line_ids.sequence,
                'product_id': self.operation_order_line_ids.product_id.id,
                'product_uom_id': self.operation_order_line_ids.product_uom.id,
                'quantity': self.operation_order_line_ids.qty,
                'price_unit': self.operation_order_line_ids.price_unit,
                'analytic_account_id': self.analytic_account_id.id,
                'equipments_id': self.operation_order_line_ids.equipments_id.id,
                'operations_id': self.id,
            })],
            'company_id': self.company_id.id,
        }
        bill = self.env['account.move'].create(invoice_vals)
        result = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_move_in_invoice_type')
        res = self.env.ref('account.view_move_form', False)
        form_view = [(res and res.id or False, 'form')]
        result['views'] = form_view + \
                          [(state, view)
                           for state, view in result['views'] if
                           view != 'form']
        result['res_id'] = bill.id
        return result


class FarmOperationsOline(models.Model):
    _name = 'farm.operations.oline'
    _description = 'Operation Order Line'

    sequence = fields.Integer(
        string='Sequence',
        default=10)
    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True,
        domain="[('categ_id', '=', categ_id), ('purchase_ok', '=', True)]",
        change_default=True)
    name = fields.Text(
        string='Description',
        required=False)
    categ_id = fields.Many2one(
        related='operations_id.category_id',
        string='Category')
    price_unit = fields.Float(
        string='Price')
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        domain="[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float(
        string='Quantity')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='operations_id.company_id',
        change_default=True,
        default=lambda self: self.env.company,
        required=False,
        readonly=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='operations_id.currency_id',
        readonly=True,
        help="Used to display the currency when tracking monetary values")
    note = fields.Char(
        string='Short Note')
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        currency_field='currency_id',
        store=True)
    invoice_lines = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='purchase_line_id',
        string="Bill Lines",
        readonly=True,
        copy=False)
    operations_id = fields.Many2one(
        comodel_name='farm.operations',
        string='Operation Order')
    state = fields.Selection(
        related='operations_id.state',
        store=True)
    equipments_id = fields.Many2one(
        comodel_name='farm.equipments',
        string='Equipment',
        related='product_id.equipments_id')
    analytic_account_id = fields.Reference(
        related='operations_id.analytic_account_id')

    @api.onchange('product_id')
    def onchange_price_unit(self):
        if not self.product_id:
            self.price_unit = 0
            return
        self.price_unit = self.product_id.standard_price

    @api.depends('price_unit', 'qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.qty
