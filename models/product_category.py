from odoo import fields, models, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    location_id = fields.Many2one(
        'stock.location',
        string = "Stock Consume Location",
        check_company = True,
        required = True)
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
        ('produce', 'Produce'),
        ('sales', 'Sales')],
        string = 'Order Type',
        readonly = False,
        copy = False)




    # @api.onchange('categ_id')
    # def _onchange_categ_id(self):
