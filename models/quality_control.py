from odoo import fields, models


class QualityControl(models.Model):
    _name = 'farm.quality.control'
    _description = 'Inspect and cure Pio Asset '

    code = fields.Char()
    name = fields.Char()
    state = fields.Selection()
    sub_action = fields.Many2many()

    me = fields.Many2one()
    init_date = fields.Date()
    parent_id = fields.Many2one
    routine = fields.Char()

    what = fields.Text()

    action = fields.Text()
    who = fields.Many2one()
    when = fields.Date()


class PioAsset(models.Model):
    _name = 'farm.pio.asset'
    _description = 'List of Pio Asset'

    code = fields.Char()
    name = fields.Char()
    type = fields.Many2one()

