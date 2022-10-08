from odoo import fields, models, api, _
from odoo.exceptions import UserError


class farm_materials(models.Model):
    _name = 'farm.materials'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Handel all operation orders'
    _order = 'issue_date'

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('materials_order_line_ids')
    def _compute_material_order_cost(self):
        for rec in self:
            oline = sum(
                self.env['farm.materials.oline'].search([('materials_id', '=', rec.id)]).mapped('price_subtotal'))
            rec.m_order_cost = oline
        return rec.m_order_cost

    def _compute_stock_move_count(self):
        for rec in self:
            materials_consumption_count = self.env['account.move'].search_count([('invoice_origin', '=', rec.name)])
            rec.materials_consumption_count = materials_consumption_count

    def _compute_stock_move_total(self):
        for rec in self:
            total = sum(
                self.env['account.move'].search([('invoice_origin', '=', rec.name)]).mapped('amount_total_signed'))
            rec.materials_consumption_total = total
        return rec.materials_consumption_total

    # -------------------------------------------------------------------------
    # Create METHODS
    # -------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('farm.materials') or _('New')
        return super(farm_materials, self).create(vals)

    def button_farm_stock_out(self):
        # create vendor bill in background and open form view.
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'direct')
        warehouse = self.stock_warehouse

        if not warehouse:
            raise UserError(_('Please define a warehouse for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        picking_vals = {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            # 'location_dest_id': self.partner_id.property_stock_customer.id,
            'location_id': self.location_id.id,
            'move_type': 'direct',
            'note': self.notes,
            'scheduled_date': self.issue_date,
            'date_deadline': self.issue_date,
            'user_id': self.user_id.id,
            'state': 'draft',
            'move_ids_without_package':[(0, 0, {
                'name': self.materials_order_line_ids.name or '',
                'product_id': self.materials_order_line_ids.product_id.id,
                'product_uom': self.materials_order_line_ids.product_uom.id,
                'location_id': self.picking_type_id.default_location_src_id.id,
                'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                # 'picking_id': picking.id,
                'state': 'draft',
                'company_id': self.company_id.id,
                'price_unit': self.materials_order_line_ids.price_unit,
                'picking_type_id': self.picking_type_id.id,
                'route_ids': 1 and [
                    (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                'warehouse_id': self.picking_type_id.warehouse_id.id,
            })]
        }
        print('here...',picking_vals)
        picking = self.env['stock.picking'].create(picking_vals)
        result = self.env.ref('stock.view_picking_form')
        res = self.env.ref('stock.view_picking_form', False)
        form_view = [(res and res.id or False, 'form')]
        result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
        result['res_id'] = picking.id
        return result
        # return


    def action_stock_picking_list(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Moves',
            'res_model': 'stock.picking',
            'domain': [('invoice_origin', '=', self.name)],
            'view_mode': 'tree,form',
            'context': {},
            'target': 'current'
        }
        print('hi')

    name = fields.Char(
        string = 'Material Ref',
        index = True,
        readonly = True,
        tracking = True,
        default = lambda x: _('New'))
    state = fields.Selection([
        ('order', 'Order'),
        ('lock', 'Locked')],
        string = 'State', readonly = False, copy = False,
        tracking = True, default = 'order')
    category_id = fields.Many2one(
        'product.category',
        required = True,
        string = 'Product Category')
    projects_id = fields.Many2one(
        'farm.projects',
        required = True,
        tracking = True)
    short_name = fields.Char(
        related = 'projects_id.short_name',
        store = True)
    issue_date = fields.Date(
        string = 'Date',
        default = fields.Datetime.today,
        tracking = True)
    partner_id = fields.Many2one(
        'res.partner',
        string = 'Partner')
    stock_warehouse = fields.Many2one(
        'stock.warehouse',
        required = True,
        string = 'Warehouse')
    location_id = fields.Many2one(
        'stock.location',
        "Source Location",
        default = lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id,
        domain = [('usage', '=', 'internal')],
        check_company = True,
        required = True)
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        "Stock Picking Type",
        default = lambda self: self.env['stock.picking.type'].search([
            ('name', '=', 'Farm Stock Consumption')]).id,
        required = True)
    m_order_cost = fields.Monetary(
        string = 'Order Cost',
        compute = '_compute_material_order_cost',
        currency_field = 'currency_id',
        store = True)
    active = fields.Boolean(
        string = "Active",
        default = True,
        tracking = True)
    user_id = fields.Many2one(
        'res.users',
        string = "Material Man",
        required = True)
    notes = fields.Html(
        'Terms and Conditions')
    materials_order_line_ids = fields.One2many(
        'farm.materials.oline',
        'materials_id',
        string = "order lines")
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
    materials_consumption_count = fields.Integer(
        string = "Material Moves Count",
        compute = '_compute_stock_move_count')
    materials_consumption_total = fields.Integer(
        string = "Material Moves Total",
        compute = '_compute_stock_move_total')


class farm_materials_oline(models.Model):
    _name = 'farm.materials.oline'
    _description = 'handel all material order line'

    @api.depends('price_unit', 'qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.qty

    name = fields.Text(
        string = 'Description',
        required = True)
    sequence = fields.Integer(
        string = 'Sequence',
        default = 10)
    product_id = fields.Many2one(
        'product.product',
        required = True,
        domain = "[('categ_id', '=', categ_id)]")
    categ_id = fields.Many2one(
        related = 'materials_id.category_id',
        string = 'Category')
    price_unit = fields.Float(
        related = 'product_id.standard_price',
        string = 'Price')
    product_uom = fields.Many2one(
        'uom.uom',
        'Unit of Measure',
        related = 'product_id.uom_id',
        domain = "[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float(
        'Quantity')
    company_id = fields.Many2one(
        'res.company',
        string = 'Company',
        related = 'materials_id.company_id',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True)
    currency_id = fields.Many2one(
        'res.currency',
        string = 'Currency',
        related = 'materials_id.currency_id',
        readonly = True,
        help = "Used to display the currency when tracking monetary values")
    note = fields.Char(
        'Short Note')
    price_subtotal = fields.Monetary(
        string = 'Subtotal',
        compute = '_compute_subtotal',
        currency_field = 'currency_id',
        store = True)
    materials_id = fields.Many2one(
        'farm.materials',
        string = 'Materials')
    equipments_id = fields.Many2one(
        'farm.equipments',
        string = 'Equipments',
        related = 'product_id.equipments_id')
