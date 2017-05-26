{
    'name': 'GI User Log',
    'category': 'General',
    'version': '0.1',
    'depends': ['base'],
    'data': [
	'users_log_view.xml',
	'security/ir.model.access.csv',
	'security/res_users_log_security.xml',
	'ir_autovacuum.xml'
    ],
    'demo': [
    ],
    'qweb': [],
    'installable': True,
}
