# -*- coding: utf-8 -*-
# from odoo import http


# class MsAgriculture(http.Controller):
#     @http.route('/ms_agriculture/ms_agriculture', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ms_agriculture/ms_agriculture/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ms_agriculture.listing', {
#             'root': '/ms_agriculture/ms_agriculture',
#             'objects': http.request.env['ms_agriculture.ms_agriculture'].search([]),
#         })

#     @http.route('/ms_agriculture/ms_agriculture/objects/<model("ms_agriculture.ms_agriculture"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ms_agriculture.object', {
#             'object': obj
#         })
