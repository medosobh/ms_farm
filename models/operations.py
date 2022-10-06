from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


class farm_operations(models.Model):
    _name = 'farm.operations'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Handel all operation orders'
    _order = 'issue_date'

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('operation_order_line_ids')
    def _compute_operation_order_cost(self):
        for rec in self:
            oline = sum(
                self.env['farm.operations.oline'].search([('operations_id', '=', rec.id)]).mapped('price_subtotal'))
            rec.o_order_cost = oline
        return rec.o_order_cost

    def _compute_vendor_bill_count(self):
        for rec in self:
            vendor_bill_count = self.env['account.move'].search_count([('invoice_origin', '=', rec.name)])
            rec.vendor_bill_count = vendor_bill_count

    def _compute_vendor_bill_total(self):
        for rec in self:
            total = sum(
                self.env['account.move'].search([('invoice_origin', '=', rec.name)]).mapped('amount_total_signed'))
            rec.vendor_bill_total = total
        return rec.vendor_bill_total

    @api.depends('operation_order_line_ids.invoice_lines.move_id')
    def _compute_invoice(self):
        for order in self:
            invoices = order.mapped('operation_order_line_ids.invoice_lines.move_id')
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    # -------------------------------------------------------------------------
    # Create METHODS
    # -------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('farm.operations') or _('New')
        return super(farm_operations, self).create(vals)

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
        # create vendor bill in background and open popup form view.
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type = move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (
            self.company_id.name, self.company_id.id))

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
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [(0, 0, {
                'sequence': self.operation_order_line_ids.sequence,
                'product_id': self.operation_order_line_ids.product_id.id,
                'product_uom_id': self.operation_order_line_ids.product_uom.id,
                'quantity': self.operation_order_line_ids.qty,
            })],
            'company_id': self.company_id.id,
        }
        bill = self.env['account.move'].create(invoice_vals)
        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        res = self.env.ref('account.view_move_form', False)
        form_view = [(res and res.id or False, 'form')]
        result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
        result['res_id'] = bill.id
        return result

    name = fields.Char(string = 'Operation Ref',
                       index = True,
                       readonly = True,
                       tracking = True,
                       default = lambda x: _('New'))
    state = fields.Selection([
        ('purchase', 'Invoicing'),
        ('done', 'Locked')
    ],
        string = 'Status',
        readonly = False,
        index = True,
        copy = False,
        tracking = True,
        default = 'purchase')
    category_id = fields.Many2one('product.category',
                                  required = True,
                                  string = 'Product Category')
    projects_id = fields.Many2one('farm.projects',
                                  required = True,
                                  tracking = True)
    short_name = fields.Char(related = 'projects_id.short_name',
                             store = True)
    issue_date = fields.Date(string = 'Date',
                             default = fields.Datetime.today,
                             tracking = True)
    partner_id = fields.Many2one('res.partner',
                                 required = True,
                                 string = 'Partner')
    payment_term_id = fields.Many2one('account.payment.term',
                                      'Payment Terms',
                                      domain = "['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    stock_warehouse = fields.Many2one('stock.warehouse',
                                      string = 'Warehouse')
    o_order_cost = fields.Monetary(string = 'Order Cost',
                                   compute = '_compute_operation_order_cost',
                                   currency_field = 'currency_id',
                                   store = True)
    active = fields.Boolean(string = "Active",
                            default = True,
                            tracking = True)
    user_id = fields.Many2one('res.users',
                              string = "Operation Man",
                              required = True)
    operation_order_line_ids = fields.One2many('farm.operations.oline',
                                                'operations_id',
                                                string = "order lines")
    notes = fields.Html('Terms and Conditions')
    company_id = fields.Many2one('res.company',
                                 string = 'Company',
                                 change_default = True,
                                 default = lambda self: self.env.company,
                                 required = False,
                                 readonly = True)
    currency_id = fields.Many2one('res.currency',
                                  'Currency',
                                  related = 'company_id.currency_id',
                                  readonly = True,
                                  ondelete = 'set null',
                                  help = "Used to display the currency when tracking monetary values")
    vendor_bill_count = fields.Integer(string = "Vendor Bill Count",
                                       compute = '_compute_vendor_bill_count')
    vendor_bill_total = fields.Integer(string = "Vendor Bill Total",
                                       compute = '_compute_vendor_bill_total')
    invoice_count = fields.Integer(compute = "_compute_invoice",
                                   string = 'Bill Count',
                                   copy = False,
                                   default = 0,
                                   store = True)
    invoice_ids = fields.Many2many('account.move',
                                   compute = "_compute_invoice",
                                   string = 'Bills',
                                   copy = False,
                                   store = True)


class farm_operations_oline(models.Model):
    _name = 'farm.operations.oline'
    _description = 'handel all operation order line'

    @api.depends('price_unit', 'qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.qty

    def _prepare_farm_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        res = {
            # 'display_type': self.display_type,
            'sequence': self.sequence,
            'name': '%s: %s' % (self.operations_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty,
            'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date,
                                                    round = False),
            # 'tax_ids': [(6, 0, self.taxes_id.ids)],
            # 'analytic_account_id': self.account_analytic_id.id,
            # 'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'purchase_line_id': self.id,
        }
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res

    sequence = fields.Integer(string = 'Sequence', default = 10)
    product_id = fields.Many2one('product.product',
                                 required = True,
                                 domain = "[('categ_id', '=', categ_id)]")
    name = fields.Text(string = 'Description',
                       required = False)
    categ_id = fields.Many2one(related = 'operations_id.category_id',
                               string = 'Category')
    price_unit = fields.Float(related = 'product_id.standard_price',
                              string = 'Price')
    product_uom = fields.Many2one(
        'uom.uom',
        'Unit of Measure',
        related = 'product_id.uom_id',
        domain = "[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float('Quantity')
    company_id = fields.Many2one('res.company',
                                 string = 'Company',
                                 related = 'operations_id.company_id',
                                 change_default = True,
                                 default = lambda self: self.env.company,
                                 required = False,
                                 readonly = True)
    currency_id = fields.Many2one(
        'res.currency',
        string = 'Currency',
        related = 'operations_id.currency_id',
        readonly = True,
        help = "Used to display the currency when tracking monetary values")
    note = fields.Char('Short Note')
    price_subtotal = fields.Monetary(
        string = 'Subtotal',
        compute = '_compute_subtotal',
        currency_field = 'currency_id',
        store = True)
    invoice_lines = fields.One2many('account.move.line',
                                    'purchase_line_id',
                                    string = "Bill Lines",
                                    readonly = True,
                                    copy = False)
    operations_id = fields.Many2one(
        'farm.operations',
        string = 'Operations')
    equipments_id = fields.Many2one(
        'farm.equipments',
        string = 'Equipments',
        related = 'product_id.equipments_id')
    state = fields.Selection(related = 'operations_id.state', store = True)


class stockPicking(models.Model):
    _inherit = 'stock.move'

    reference_record = fields.Reference(selection = [('farm.operations', 'Operation Order'),
                                                     ('farm.produce', 'Produce Order')],
                                        string = 'Order Reference')
