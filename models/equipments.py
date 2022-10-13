from odoo import fields, models, _
from odoo.exceptions import UserError


class farm_equipments(models.Model):
    _name = 'farm.equipments'
    _description = 'Manage all Equipments'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('code_uniq', 'unique(code)', "A code can only be assigned to one equipments !"),
        ('name_uniq', 'unique(name)', "A name can only be assigned to one equipments !"),
        ('product_id', 'unique(product_id)', "A one service product can only be assigned to one equipment !"),
    ]

    # create a related product under equipment category
    # to use in operation order
    def create_equipment_product(self):
        # if it is existed and send error message
        new_name = self.code + " " + self.type + " " + self.name
        search_name = self.env['product.template'].search([
            ('name', '=', new_name)])
        if search_name:
            raise UserError(_('Product already exist in the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        # elif create
        product_vals = {
            'categ_id': self.env.ref('ms_farm.product_category_equipment').id,
            'detailed_type': 'service',
            'name': new_name,
            'equipments_id': self.id,
        }
        new_product = self.env['product.template'].create(product_vals)
        # link service product to equipment
        self.product_id = new_product.id
        return

    def action_action(self):
        print('action')

    def _compute_order_line_count(self):
        for rec in self:
            count = self.env['farm.operations.oline'].search_count([
                ('equipments_id', '=', rec.id)])
            rec.order_line_count = count
        return rec.order_line_count

    def _compute_order_cost(self):
        for rec in self:
            cost = sum(
                self.env['farm.operations.oline'].search([
                    ('equipments_id', '=', rec.id)
                ]).mapped('price_subtotal'))
            rec.order_line_cost = cost
        return rec.order_line_cost

    def _compute_actual_cost(self):
        for record in self:
            costa = sum(
                self.env['farm.operations.oline'].search([
                    ('product_id', '=', record.product_id)
                ]).mapped('price_subtotal'))
            record.actual_line_cost = costa
        return record.actual_line_cost

    def update_equipment_product_price_unit(self):
        if self.product_id:
            update = self.env['product.template'].browse(
                self.product_id.id).write({
                'standard_price': self.buy_sell_price,
                'list_price': self.buy_sell_price,
                'equipments_id': self.id,
                'categ_id': self.env.ref('ms_farm.product_category_equipment').id,
                'detailed_type': 'service'
            })
            print(update)
        return update

    code = fields.Char(
        string = 'Internal Code',
        required = True)
    name = fields.Char(
        string = 'Name',
        required = True)
    description = fields.Text(
        'description')
    type = fields.Selection([
        ('device', 'Device'),
        ('truck', 'Truck'),
        ('vehicle', 'Vehicle')
    ],
        required = True)
    body_code = fields.Char(
        string = 'Body Code',
        required = True)
    product_id = fields.Many2one(
        'product.product',
        domain = "[('categ_id', '=', category_id)]",
        store = True)
    acq_date = fields.Date(
        string = 'Acquisition Date',
        required = True)
    active = fields.Boolean(
        string = "Active",
        default = True,
        tracking = True)
    category_id = fields.Many2one(
        'product.category',
        required = True,
        default = lambda self: self.env.ref('ms_farm.product_category_equipment'),
        string = 'Product Category')
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
    buy_sell_price = fields.Float(
        string = 'buy  and sell price',
        store = True)
    order_line_count = fields.Integer(
        string = '# of Order',
        compute = '_compute_order_line_count',
        store = True)
    order_line_cost = fields.Monetary(
        string = 'Order Cost',
        compute = '_compute_order_cost',
        store = True)
    actual_line_cost = fields.Monetary(
        string = 'Actual Cost',
        compute = '_compute_actual_cost',
        store = True)
    operation_order_line_ids = fields.One2many(
        'farm.operations.oline',
        'equipments_id',
        string = "order lines")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    equipments_id = fields.Many2one(
        'farm.equipments',
        string = 'Equipments',
        readonly = True)
