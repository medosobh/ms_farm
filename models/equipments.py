from odoo import fields, models, _
from odoo.exceptions import UserError


class farm_equipments(models.Model):
    _name = 'farm.equipments'
    _description = 'Manage all Equipments'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('code_uniq', 'unique(code)', "A code can only be assigned to one equipments !"),
        ('name_uniq', 'unique(name)', "A name can only be assigned to one equipments !"),
    ]

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
        compute = '_compute_order_line_count')
    order_line_cost = fields.Monetary(
        string = 'Order Cost',
        compute = '_compute_order_cost')
    total_expense = fields.Monetary(
        string = 'Actual Cost',
        compute = '_compute_total_expense')
    operation_order_line_ids = fields.One2many(
        'farm.operations.oline',
        'product_id',
        domain =
        "[('product_id', '=', product_id.id)]",
        readonly = True,
        string = "Order lines")
    operation_actual_line_ids = fields.One2many(
        'account.move.line',
        'equipments_id',
        domain =
        "[('equipments_id', '=', id)]",
        readonly = True,
        string = "Actual lines"
    )

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
        product_vals = dict(
            categ_id = self.category_id.id,
            detailed_type = 'service',
            name = new_name,
            equipments_id = self.id,
            default_code = self.code + " " + self.name,
            standard_price = self.buy_sell_price,
            list_price = self.buy_sell_price,
        )
        new_product = self.env['product.template'].create(product_vals)
        return new_product

    def action_action(self):
        print('action')

    def _compute_order_line_count(self):
        for rec in self:
            count = self.env['farm.operations.oline'].search_count([
                ('equipments_id', '=', rec.id)
            ])
            rec.order_line_count = count
        return rec.order_line_count

    def _compute_order_cost(self):
        for rec in self:
            cost = sum(
                self.env['farm.operations.oline'].search([
                    ('equipments_id', '=', rec.id)
                ]).mapped('price_subtotal')
            )
            rec.order_line_cost = cost
        return rec.order_line_cost

    def _compute_total_expense(self):
        for rec in self:
            cost_debit = sum(
                self.env['account.move.line'].search([
                    ('equipments_id', '=', rec.id)
                ]).mapped('debit'))
            cost_credit = sum(
                self.env['account.move.line'].search([
                    ('equipments_id', '=', rec.id)
                ]).mapped('credit'))
            rec.total_expense = cost_debit - cost_credit
        return rec.total_expense
