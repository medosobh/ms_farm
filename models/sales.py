from odoo import fields, models, api, _


class farm_sales(models.Model):
    _name = 'farm.sales'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Handel all sales order'
    _order = 'issue_date'

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('farm_sales_oline_ids')
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
        print('hi')

    name = fields.Char(string = 'Sales Ref',
                       index = True,
                       readonly = True,
                       tracking = True,
                       default = lambda x: _('New'))
    state = fields.Selection([
        ('order', 'Order'),
        ('document', 'Document')],
        string = 'State', readonly = False, copy = False,
        tracking = True, default = 'order')
    category_id = fields.Many2one('product.category',
                                  required = True,
                                  string = 'Product Category')
    projects_id = fields.Many2one('farm.projects',
                                  required = True,
                                  tracking = True)
    short_name = fields.Char(related = 'projects_id.short_name',
                             store = True)
    issue_date = fields.Date(string = 'Date', default = fields.Datetime.today, tracking = True)
    partner_id = fields.Many2one('res.partner',
                                 string = 'Partner')
    stock_warehouse = fields.Many2one('stock.warehouse',
                                      string = 'Warehouse')
    s_order_cost = fields.Float(string = 'Order Cost',
                                compute = '_compute_sales_order_cost',
                                store = True)
    active = fields.Boolean(string = "Active", default = True, tracking = True)
    user_id = fields.Many2one('res.users',
                              string = "Operation Man",
                              required = True)
    farm_sales_oline_ids = fields.One2many('farm.sales.oline',
                                           'sales_id',
                                           string = "order lines")
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
    customer_invoice_count = fields.Integer(string = "Customer Invoice Count",
                                            compute = '_compute_customer_invoice_count')
    customer_invoice_total = fields.Integer(string = "Customer Invoice Total",
                                            compute = '_compute_customer_invoice_total')


class farm_sales_oline(models.Model):
    _name = 'farm.sales.oline'
    _description = 'handel all sales order'

    @api.depends('price_unit', 'qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.qty

    name = fields.Text(string = 'Description', required = True)
    sequence = fields.Integer(string = 'Sequence', default = 10)
    product_id = fields.Many2one('product.product',
                                 required = True,
                                 domain = "[('categ_id', '=', categ_id)]")
    categ_id = fields.Many2one(related = 'sales_id.category_id',
                               string = 'Category')
    price_unit = fields.Float(related = 'product_id.list_price',
                              string = 'Price')
    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related = 'product_id.uom_id',
        domain = "[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float('Quantity')
    company_id = fields.Many2one('res.company',
                                 string = 'Company',
                                 related = 'sales_id.company_id',
                                 change_default = True,
                                 default = lambda self: self.env.company,
                                 required = False,
                                 readonly = True)
    currency_id = fields.Many2one('res.currency',
                                  string = 'Currency',
                                  related = 'sales_id.currency_id',
                                  readonly = True,
                                  help = "Used to display the currency when tracking monetary values")
    note = fields.Char('Short Note')
    price_subtotal = fields.Monetary(string = 'Subtotal',
                                     compute = '_compute_subtotal',
                                     currency_field = 'currency_id',
                                     store = True)
    sales_id = fields.Many2one('farm.sales',
                               string = 'Sales Order')
