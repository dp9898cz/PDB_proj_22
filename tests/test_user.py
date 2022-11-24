
from http import HTTPStatus
from json import loads

from helpers import (
	ClientWrapper,
	assert_error_response, assert_ok_created,
)
from data import user_customer_Customer

class TestUser:
	NEW_USER = {
		'id': 0,
		'first_name': 'First',
		'last_name': 'Last',
		'email': 'new_email@email.cz',
		'password': 'password123'
	}

	def test_register(self, client: ClientWrapper):
		data = {
			'first_name': TestUser.NEW_USER['first_name'],
			'last_name': TestUser.NEW_USER['last_name'],
			'email': TestUser.NEW_USER['email'],
			'password': TestUser.NEW_USER['password']
		}

		resp = client.post('/register', data)
		assert_ok_created(resp.status_code)
		json_data = loads(resp.data.decode())
		assert 'id' in json_data

		TestUser.NEW_USER['id'] = json_data['id']

	def test_register_invalid(self, client: ClientWrapper):
		template = {
			'first_name': 'Invalid',
			'last_name': 'Registration',
			'email': 'another_email@email.cz',
			'password': '123password'
		}

		# missing email
		data = template.copy()
		data['email'] = None
		resp = client.post('/register', data)
		assert_error_response(resp)

		# duplicate email
		data = template.copy()
		data['email'] = TestUser.NEW_USER['email']
		resp = client.post('/register', data)
		assert_error_response(resp)

		# missing password
		data = template.copy()
		data['password'] = None
		resp = client.post('/register', data)
		assert_error_response(resp)

	def test_login(self, client: ClientWrapper):
		data = {
			'email': TestUser.NEW_USER['email'],
			'password': TestUser.NEW_USER['password']
		}

		resp = client.post('/login', data)
		assert resp.status_code == HTTPStatus.OK

	def test_profile_edit(self, client: ClientWrapper):
		data = {
			'first_name': 'Edited-first-name',
			'last_name': 'Edited-last-name'
		}

		resp = client.put('/profile', data)
		assert resp.status_code == HTTPStatus.OK

		resp = client.get('/profile')
		assert resp.status_code == HTTPStatus.OK
		profile = loads(resp.data.decode())
		assert profile['first_name'] == data['first_name']
		assert profile['last_name'] == data['last_name']

	def test_logout(self, client: ClientWrapper):
		resp = client.post('/logout', {})
		assert resp.status_code == HTTPStatus.OK

	def test_login_logout_profile_access(self, client: ClientWrapper):
		data = {
			'email': TestUser.NEW_USER['email'],
			'password': TestUser.NEW_USER['password']
		}

		resp = client.post('/login', data)
		assert resp.status_code == HTTPStatus.OK

		resp = client.get('/profile')
		assert resp.status_code == HTTPStatus.OK
		json_data = loads(resp.data.decode())
		assert json_data['first_name'] == TestUser.NEW_USER['first_name']

		resp = client.post('/logout', {})
		assert resp.status_code == HTTPStatus.OK

		resp = client.get('/profile')
		assert resp.status_code == HTTPStatus.UNAUTHORIZED

	def test_client_login_logout_profile_access(self, client: ClientWrapper):
		USER = user_customer_Customer
		client.login(user=USER)

		resp = client.get('/profile')
		assert resp.status_code == HTTPStatus.OK
		json_data = loads(resp.data.decode())
		assert json_data['first_name'] == USER['first_name']

		client.logout()

		resp = client.get('/profile')
		assert resp.status_code == HTTPStatus.UNAUTHORIZED
