from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    location_id = fields.Many2one(
        'stock.location',
        string = "Stock Consume Location",
        check_company = True,
        required = False)
    company_id = fields.Many2one(
        'res.company',
        string = 'Company',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True)
    type = fields.Selection([
        ('product', 'Storable Product'),
        ('service', 'Service'),
        ('consu', 'Consumable')],
        string = 'Product Type',
        readonly = False,
        copy = False,
        default = 'product')
    order_type = fields.Selection([
        ('service', 'Service'),
        ('material', 'Material'),
        ('expense', 'Expense'),
        ('produce', 'Produce'),
        ('sales', 'Sales')],
        string = 'Order Type',
        readonly = False,
        copy = False)

class ProductTemplate(models.Model):
        _inherit = "product.template"

        reference_record = fields.Reference([
            ('farm.projects', 'Projects'),
            ('farm.equipments', 'Equipments')
        ],
            string = 'Related Module'
        )
