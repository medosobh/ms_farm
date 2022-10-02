from odoo import fields, models, api


class farm_equipments(models.Model):
    _name = 'farm.equipments'
    _description = 'Manage all Equipments'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('code_uniq', 'unique(code)', "A code can only be assigned to one equipments !"),
        ('name_uniq', 'unique(name)', "A name can only be assigned to one equipments !"),
        ('product_id', 'unique(product_id)', "A one service product can only be assigned to one equipment !"),
    ]

    code = fields.Char(string = 'Internal Code',
                       required = True)
    name = fields.Char(string = 'Name',
                       required = True)
    description = fields.Text('description')
    type = fields.Selection([
        ('device', 'Device'),
        ('truck', 'Truck'),
        ('vehicle', 'Vehicle')
    ])
    body_code = fields.Char(string = 'Body Code',
                            required = True)
    product_id = fields.Many2one('product.product',
                                 store = True)
    acq_date = fields.Date(string = 'Acquisition Date',
                           required = True)
    active = fields.Boolean(string = "Active",
                            default = True,
                            tracking = True)
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
    total_order_cost = fields.Monetary(string = 'total orders',
                                       compute = '_compute_total_orders',
                                       currency_field = 'currency_id',
                                       store = True)
    operation_order_line_ids = fields.One2many('farm.operations.oline',
                                                'equipments_id',
                                                string = "order lines")

    @api.depends('product_id')
    def _compute_total_orders(self):
        for rec in self:
            oline = 10
            # oline = sum(
            #     self.env['farm.operations.oline'].search([]).mapped('price_subtotal'))
            rec.total_order_cost = oline
        return rec.total_order_cost


class ProductTemplate(models.Model):
    _inherit = "product.template"

    equipments_id = fields.Many2one(
        'farm.equipments',
        string = 'Equipments')
