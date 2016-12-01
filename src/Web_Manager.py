# -*- coding: utf-8 -*-
# !/usr/bin/python

import os

from flask import Flask, request, session, redirect, url_for, abort, render_template, flash, current_app
from Config import GetTheConfig, WriteTheConfig
from app.storage.Database import now, executeNcommit, executeNfetchall
from src.app.search.SearchManager import RegularSearch
from flask_paginate import Pagination, get_page_args
from src.app.schedule.ScheduleManager import  StartingSchedule

app = Flask(__name__)

app.config.update(dict(
	DEBUG=True,
	SECRET_KEY='development key',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

os.chdir(os.path.dirname(os.path.abspath( __file__ ))) # 작업 경로 변경


@app.route('/')
@app.route('/page', methods=['GET'])
def show_keyword(error=None):
	keywordPage = request.args.get('keywordPage', default=1, type=int)
	sitePage = request.args.get('sitePage', default=1, type=int)

	page, per_page, offset = get_page_args()
	keywords = executeNfetchall(GetTheConfig('query', 'SELECT_KEYWORD_RESEARCH'))
	sites = executeNfetchall(GetTheConfig('query', 'SELECT_SITE_RESEARCH'))
	schedule = {"time": GetTheConfig('schedule', 'HOUR')}  # 스케쥴

	keywordTotal = executeNfetchall(GetTheConfig('query',"keywordTotal"))[0]["count(*)"] # 저장된 keyword 총 개수
	siteTotal = executeNfetchall(GetTheConfig('query', "siteTotal"))[0]["count(*)"]  # 저장된 site 총 개수

	keywordPagination = Pagination(
		css_framework=GetTheConfig('manager', 'css_framework'),
		link_size=GetTheConfig('manager', 'link_size'),
		show_single_page=GetTheConfig('manager', 'single_page_or_not'),
		page=keywordPage,
		per_page=per_page,
		total=keywordTotal,
		href="page/keywordPage={0}",
		record_name='Keyword',
		format_total=True,
		format_number=True,
		)

	sitePagination = Pagination(
		css_framework=GetTheConfig('manager', 'css_framework'),
		link_size=GetTheConfig('manager', 'link_size'),
		show_single_page=GetTheConfig('manager', 'single_page_or_not'),
		page=sitePage,
		per_page=per_page,
		total=siteTotal,
		record_name='Domain',
		format_total=True,
		format_number=True,
		)

	return render_template('show_entries.html'
						   , keywords=keywords
						   , sites=sites
						   , schedule=schedule
						   , error=error
						   , page=page
						   , per_page=per_page
						   , keywordPagination=keywordPagination
						   , sitePagination=sitePagination)


@app.route('/keyword/add', methods=['POST'])
def add_keyword():
	if not session.get('logged_in'):
		abort(401)
	keyword = request.form['keyword']

	if keyword == '' :
		error = GetTheConfig('string', 'Blank_KEYWORD')
		return show_keyword(error=error)

	storedKeywords = executeNfetchall(GetTheConfig('query', 'SELECT_KEYWORD_RESEARCH'))
	for row in storedKeywords:
		if (keyword == row['keyword']):
			error = GetTheConfig('string', 'DUPLICATE_KEYWORD')
			return show_keyword(error=error)

	executeNcommit(GetTheConfig('query', 'INSERT_KEYWORD')
				   , (keyword, 0, now()))
	flash(GetTheConfig('string', 'INSERT_KEYWORD'))
	return redirect(url_for('show_keyword'))


@app.route('/keyword/delete', methods=['POST'])
def delete_keyword():
	if not session.get('logged_in'):
		abort(401)
	idx = request.form['idx']
	executeNcommit(GetTheConfig('query', 'DELETE_KEYWORD')
				   , idx)
	flash(GetTheConfig('string', 'DELETE_KEYWORD'))
	return redirect(url_for('show_keyword'))


@app.route('/schedule/edit', methods=['POST'])
def edit_schedule():
	if not session.get('logged_in'):
		abort(401)
	time = request.form['time']
	WriteTheConfig('schedule', 'HOUR', time)
	flash(GetTheConfig('string', 'EDIT_SCHEDULE'))
	return redirect(url_for('show_keyword'))
	

@app.route('/schedule/run', methods=['POST'])
def run_schedule():
	if not session.get('logged_in'):
		abort(401)
	result = RegularSearch()

	if result == True:
		flash(GetTheConfig('string', 'RUN_SCHEDULE'))
	elif result == False:
		flash(GetTheConfig('string', 'NON_SAVED'))
	return redirect(url_for('show_keyword'))

@app.route('/schedule/execute', methods=['POST'])
def execute_schedule():
	if not session.get('logged_in'):
		abort(401)
	result = StartingSchedule()

	if result == True:
		flash(GetTheConfig('string', 'RUN_SCHEDULE'))
	elif result == False:
		flash(GetTheConfig('string', 'NON_SAVED'))
	return redirect(url_for('show_keyword'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['username'] != GetTheConfig('manager', 'USERNAME'):
			error = GetTheConfig('string', 'ERROR_USERNAME')
		elif request.form['password'] != GetTheConfig('manager', 'PASSWORD'):
			error = GetTheConfig('string', 'ERROR_PASSWORD')
		else:
			session['logged_in'] = True
			flash(GetTheConfig('string', 'LOGIN'))
			return redirect(url_for('show_keyword'))
	return render_template('login.html', error=error)


@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash(GetTheConfig('string', 'LOGOUT'))
	return redirect(url_for('show_keyword'))


if __name__ == '__main__':
	app.run()