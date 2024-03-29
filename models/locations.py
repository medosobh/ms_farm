from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FarmLocations(models.Model):
    _name = 'farm.locations'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Manage project location'
    _check_company_auto = True
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(
        string='Location',
        required=True)
    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        recursive=True,
        store=True)
    address = fields.Text(
        string='Address',
        help="Wrtie down the address of this location")
    space = fields.Float(
        string='Space in acre',
        help="The Acre space under this location (Does not consider the children location)")
    space_sum = fields.Float(
        string='Total Space in acre',
        compute='_compute_space',
        inverse='_compute_space',
        help="The Acre space under this location (Does not consider the children location)")
    parent_id = fields.Many2one(
        comodel_name='farm.locations',
        string='Parent Location',
        index=True,
        ondelete='cascade')
    parent_path = fields.Char(
        index=True)
    child_id = fields.One2many(
        comodel_name='farm.locations',
        inverse_name='parent_id',
        string='Child location')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        change_default=True,
        default=lambda self: self.env.company,
        required=False,
        readonly=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
        ondelete='set null',
        help="Used to display the currency when tracking monetary values")

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = '%s / %s' % (
                    location.parent_id.complete_name, location.name)
            else:
                location.complete_name = location.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    def name_get(self):
        if not self.env.context.get('hierarchical_naming', True):
            return [(record.id, record.name) for record in self]
        return super().name_get()

    def _compute_space(self):
        for rec in self:
            if rec.child_id:
                total = sum(
                    self.env['farm.locations'].search([
                        ('parent_id', '=', rec.id)
                    ]).mapped('space')
                )
                rec.space_sum = total
                rec.space = total
            else:
                rec.space_sum = rec.space


class FarmLocationUsed(models.Model):
    _name = 'farm.location.used'
    _description = 'Location Used'

    projects_id = fields.Many2one(
        comodel_name='farm.projects',
        string='Project',
    )
    locations_id = fields.Many2one(
        comodel_name='farm.locations',
        string='Location',
        required=True)
    space_sum = fields.Float(
        related='locations_id.space_sum')
    complete_name = fields.Char(
        related='locations_id.complete_name')
    address = fields.Text(
        related='locations_id.address')
