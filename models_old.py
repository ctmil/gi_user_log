# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2014 OpenERP s.a. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import itertools
import logging
from functools import partial
from itertools import repeat

from lxml import etree
from lxml.builder import E

import openerp
from openerp import SUPERUSER_ID, models
from openerp import tools
import openerp.exceptions
from openerp import api
from openerp.osv import fields, osv, expression
from openerp.service.security import check_super
from openerp.tools.translate import _
from openerp.http import request
import datetime

_logger = logging.getLogger(__name__)

# Only users who can modify the user (incl. the user herself) see the real contents of these fields
USER_PRIVATE_FIELDS = ['password']

class ResUsersLog(osv.Model):
    _name = 'res.users.log'
    _order = 'id desc'
    # Currenly only uses the magical fields: create_uid, create_date,
    # for recording logins. To be extended for other uses (chat presence, etc.)


class res_users(osv.osv):
    _inherit = 'res.users'

    log_ids = openerp.fields.One2many('res.users.log', 'create_uid', string='User log entries')
    login_date = openerp.fields.Datetime(related='log_ids.create_date', string='Latest connection')

    def _login(self, db, login, password):
        if not password:
            return False
        user_id = False
        try:
            with self.pool.cursor() as cr:
                res = self.search(cr, SUPERUSER_ID, [('login','=',login)])
                if res:
                    user_id = res[0]
                    self.check_credentials(cr, user_id, password)
		    if user_id != SUPERUSER_ID:
	                    self._update_last_login(cr, user_id)
		    right_now = datetime.datetime.now()
		    user = self.pool.get('res.users').browse(cr,SUPERUSER_ID,user_id)
		    if user.from_time > 0 and user.to_time < 24:
			hour = right_now.hour
			if hour < user.from_time or hour > user.to_time:
			    raise openerp.exceptions.ValidationError('No tiene permitido ingresar en este horario')
			    user_id = False				

        except openerp.exceptions.AccessDenied:
            _logger.info("Login failed for db:%s login:%s", db, login)
            user_id = False

        return user_id

    def _update_last_login(self, cr, uid):
        # only create new records to avoid any side-effect on concurrent transactions
        # extra records will be deleted by the periodical garbage collection
        self.pool['res.users.log'].create(cr, uid, {}) # populated by defaults


class AutoVacuum(models.TransientModel):
    """ Expose the vacuum method to the cron jobs mechanism. """
    _name = 'ir.autovacuum'


    def _gc_transient_models(self, cr, uid, *args, **kwargs):
        for model in self.pool.itervalues():
            if model.is_transient():
                model._transient_vacuum(cr, uid, force=True)

    def _gc_user_logs(self, cr, uid, *args, **kwargs):
        cr.execute("""
            DELETE FROM res_users_log log1 WHERE EXISTS (
                SELECT 1 FROM res_users_log log2
                WHERE log1.create_uid = log2.create_uid
                AND log1.create_date < log2.create_date
            )
        """)
        _logger.info("GC'd %d user log entries", cr.rowcount)

    def power_on(self, cr, uid, *args, **kwargs):
        self._gc_transient_models(cr, uid, *args, **kwargs)
        #self._gc_user_logs(cr, uid, *args, **kwargs)
        return True

