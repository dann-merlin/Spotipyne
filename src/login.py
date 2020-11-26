# login.py
#
# Copyright 2020 Merlin Danner
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GLib

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import WebDriverException

import threading
import os
from .spotify import Spotify as sp
import spotipy

@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/login.ui')
class Login(Gtk.Bin):
	__gtype_name__ = 'Login'

	LoginListBox = Gtk.Template.Child()

	def __init__(self, onLoggedIn, **kwargs):
		super().__init__(**kwargs)
		if self.canLogIn():
			GLib.idle_add(onLoggedIn)
			return

		try:
			sp.delete_cached_token()
		except FileNotFoundError:
			pass

		def installTrapBrowser():
			import webbrowser
			webbrowser.register(name="echo", klass=None, instance=webbrowser.Mozilla("echo"), preferred=True)
		installTrapBrowser()

		self.onLoggedIn = onLoggedIn
		self.SubmitButton = Gtk.Button("Submit")
		username_label = Gtk.Label('Username: ')
		username_input = Gtk.Entry()
		username_input.set_placeholder_text('Input username here')
		box_username = Gtk.FlowBox()
		box_username.set_homogeneous(True)
		box_username.add(username_label)
		box_username.add(username_input)
		password_label = Gtk.Label('Password: ')
		password_input = Gtk.Entry()
		password_input.set_placeholder_text('Input password here')
		password_input.set_visibility(False)
		password_input.set_invisible_char('*')
		box_password = Gtk.FlowBox()
		box_password.set_homogeneous(True)
		box_password.add(password_label)
		box_password.add(password_input)
		self.LoginListBox.add(Gtk.Label("Login to Spotify"))
		self.LoginListBox.add(box_username)
		self.LoginListBox.add(box_password)
		self.LoginListBox.add(self.SubmitButton)
		self.show_all()
		def onButtonPressed(button):
			def readInputsAndStartLoginThread():
				threading.Thread(daemon=True, target=self.loginWithSelenium, args=(username_input.get_text(), password_input.get_text())).start()
			GLib.idle_add(readInputsAndStartLoginThread)
		self.SubmitButton.connect("clicked", onButtonPressed)

	def canLogIn(self):
		try:
			auth_manager = sp.build_auth_manager()
		except Exception as e:
			# Probably username is not cached
			return False
		cached_token = auth_manager.get_cached_token()
		if cached_token is None:
			return False
		if auth_manager.is_token_expired(cached_token):
			# get_cached_token already tries to refresh the token if it is expired.
			# No need to try again.
			return False
		return True

	def loginWithSelenium(self, username, password):
		sp.set_username_backup(username)
		start_auth = threading.Semaphore()

		def handleLoginRequest():
			def getWebdriver():
				try:
					return webdriver.Firefox()
				except:
					print("Firefox driver (geckodriver) not installed", file=sys.stderr)
				try:
					return webdriver.Chrome()
				except WebDriverException:
					print("Chrome driver is not installed", file = sys.stderr)
				try:
					return webdriver.Safari()
				except Exception:
					print("Safari driver is not installed", file = sys.stderr)
				try:
					return webdriver.Ie()
				except WebDriverException:
					print("Internet Explorer driver is not installed", file = sys.stderr)
				raise Exception("No installed Webdriver found")

			def handleLoginPage(driver, url):
				driver.get(url)
				site_load_timeout = 3
				def logIntoAccount():
					WebDriverWait(driver, site_load_timeout).until(expected_conditions.element_to_be_clickable((By.ID, "login-button")))
					driver.find_element_by_id("login-username").send_keys(username)
					driver.find_element_by_id("login-password").send_keys(password)
					driver.find_element_by_id("login-button").click()
				def authorizeRequest():
					def auth_cond(driver):
						return ( "Authorize" in driver.title and driver.find_element_by_id("auth-accept") is not None) or "Authentication status: success" in driver.page_source

					WebDriverWait(driver, site_load_timeout).until(auth_cond)
					if "Authentication status: success" in driver.page_source:
						print("Application is already authorized")
					else:
						try:
							driver.find_element_by_id("auth-accept").click()
							print("Authorization granted!")
						except WebDriverException:
							print("Failed to authorize on the spotify web page")
							return False
					return True

				if "Login" in driver.title:
					logIntoAccount()

				WebDriverWait(driver, site_load_timeout).until_not(expected_conditions.title_contains("Login"))
				authorized = authorizeRequest()
				driver.quit()
				return authorized

			start_auth.acquire(1)
			url = sp.build_auth_manager().get_authorize_url()
			try:
				return handleLoginPage(getWebdriver(), url)
			except Exception:
				print("Failed logging in.")
				return False
				# TODO try again somehow

		def _login_browser():
			sp.get().currently_playing()
			start_auth.release()
		threading.Thread(daemon=True, target=_login_browser).start()

		handleLoginRequest()

		sp.save_username_to_cache(username)

		GLib.idle_add(self.onLoggedIn)
