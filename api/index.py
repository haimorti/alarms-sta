from __future__ import annotations

from flask import Flask, Response, jsonify, request

from src.app.bootstrap import bootstrap_application
from src.config.settings import AppSettings
from src.ui.pages import render_home_page, render_settlement_page

app = Flask(__name__)
artifacts = bootstrap_application(AppSettings.from_env())


@app.get('/')
def home() -> Response:
    return Response(
        render_home_page(artifacts.api_service.health(), artifacts.api_service.events_active()),
        mimetype='text/html; charset=utf-8',
    )


@app.get('/health')
def health() -> Response:
    return jsonify(artifacts.api_service.health())


@app.get('/events/active')
def events_active() -> Response:
    return jsonify(artifacts.api_service.events_active())


@app.get('/settlements/search')
def settlements_search() -> Response:
    return jsonify(artifacts.api_service.settlements_search(request.args.get('q', '')))


@app.get('/probability/current')
def probability_current() -> Response:
    payload = artifacts.api_service.probability_current(request.args.get('settlement', '')) or {}
    if request.args.get('format', 'json') == 'html':
        return Response(render_settlement_page(payload), mimetype='text/html; charset=utf-8')
    return jsonify(payload)
