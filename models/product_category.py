from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'
    _description = 'Product Category'

    location_id = fields.Many2one(
        'stock.location',
        'id',
        string = "Stock Consume Location",
        check_company = True,
        required = True)
