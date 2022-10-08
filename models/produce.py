from odoo import fields, models, api, _


class farm_produce(models.Model):
    _name = 'farm.produce'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Handel all produce order'
    _order = 'issue_date'

    @api.depends('produce_order_line_ids')
    def _compute_produce_order_cost(self):
        self.p_order_cost = 0
        for rec in self:
            pline = sum(self.env['farm.produce.oline'].search([('produce_id', '=', rec.id)]).mapped('price_subtotal'))
            rec.p_order_cost = pline
        return rec.p_order_cost

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('farm.produce') or _('New')
        return super(farm_produce, self).create(vals)

    def button_farm_stock_in(self):
        print('hi')

    name = fields.Char(string = 'Produce Ref',
                       index = True,
                       readonly = True,
                       tracking = True,
                       default = lambda x: _('New'))
    state = fields.Selection([
        ('order', 'Invoicing'),
        ('lock', 'Locked')],
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
    p_order_cost = fields.Float(string = 'Order Cost',
                                compute = '_compute_produce_order_cost',
                                store = True)
    active = fields.Boolean(string = "Active", default = True, tracking = True)
    user_id = fields.Many2one('res.users',
                              string = "Operation Man",
                              required = True)
    produce_order_line_ids = fields.One2many('farm.produce.oline',
                                             'produce_id',
                                             string = "produce order lines")
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


class farm_produce_oline(models.Model):
    _name = 'farm.produce.oline'
    _description = 'handel all produce order line'

    @api.depends('price_unit', 'qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.qty

    name = fields.Text(string = 'Description', required = True)
    sequence = fields.Integer(string = 'Sequence', default = 10)
    product_id = fields.Many2one('product.product',
                                 required = True,
                                 domain = "[('categ_id', '=', categ_id)]")
    categ_id = fields.Many2one(related = 'produce_id.category_id',
                               string = 'Category')
    # check! calculate price from total cost.
    price_unit = fields.Float(related = 'product_id.standard_price',
                              string = 'Price')
    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related = 'product_id.uom_id',
        domain = "[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float('Quantity')
    company_id = fields.Many2one('res.company',
                                 string = 'Company',
                                 related = 'produce_id.company_id',
                                 change_default = True,
                                 default = lambda self: self.env.company,
                                 required = False,
                                 readonly = True)
    currency_id = fields.Many2one('res.currency',
                                  string = 'Currency',
                                  related = 'produce_id.currency_id',
                                  readonly = True,
                                  help = "Used to display the currency when tracking monetary values")
    note = fields.Char('Short Note')
    price_subtotal = fields.Monetary(string = 'Subtotal',
                                     compute = '_compute_subtotal',
                                     currency_field = 'currency_id',
                                     store = True)
    produce_id = fields.Many2one('farm.produce', string = 'Produce Order')
