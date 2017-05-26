# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.osv import osv
from openerp.exceptions import except_orm, ValidationError
from StringIO import StringIO
import urllib2, httplib, urlparse, gzip, requests, json
import openerp.addons.decimal_precision as dp
import logging
import datetime
from openerp.fields import Date as newdate
from datetime import datetime, timedelta, date
from dateutil import relativedelta
#Get the logger
_logger = logging.getLogger(__name__)

class res_users(models.Model):
	_inherit = 'res.users'

	@api.constrains('from_time','to_time')
	def _check_time_constrains(self):
		if self.from_time < 0 or self.from_time > 24:
			raise ValidationError('La hora desde debe ser una hora valida')
		if self.to_time < 0 or self.to_time > 24:
			raise ValidationError('La hora hasta debe ser una hora valida')
		if self.to_time <= self.from_time:
			raise ValidationError('La hora hasta debe ser mayor a la hora desde')

	from_time = fields.Integer('Hora desde',default=0)
	to_time = fields.Integer('Hora hasta',default=24)

