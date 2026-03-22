from __future__ import annotations

from html import escape
from typing import Any


def render_home_page(health: dict[str, Any], active_events: list[dict[str, Any]]) -> str:
    event_items = "".join(
        f"<li>#{event['id']} — {escape(str(event['normalized_type']))} — {escape(str(event['started_at']))}</li>"
        for event in active_events[:10]
    ) or "<li>No events available</li>"
    return f"""
    <html><body>
      <h1>Alarms STA</h1>
      <h2>Source status</h2>
      <p>Status: {escape(str(health.get('status')))}</p>
      <p>Last fetch: {escape(str(health.get('last_fetch_at')))}</p>
      <h2>Active events</h2>
      <ul>{event_items}</ul>
      <h2>Settlement lookup</h2>
      <p>Use <code>/probability/current?settlement=&lt;name&gt;&amp;format=html</code>.</p>
    </body></html>
    """


def render_settlement_page(payload: dict[str, Any]) -> str:
    settlement = payload.get("settlement", {})
    snapshot = payload.get("snapshot", {})
    if not snapshot:
        return f"<html><body><h1>{escape(str(settlement.get('name_he', 'Unknown')))}</h1><p>{escape(str(payload.get('message', 'No probability snapshot available')))}</p></body></html>"
    return f"""
    <html><body>
      <h1>{escape(str(settlement.get('name_he')))}</h1>
      <p>Settlement is inside active early warning: yes</p>
      <p>Actual alarm already present: unknown / cluster dependent</p>
      <h2>Probability breakdown</h2>
      <ul>
        <li>Spatial probability: {escape(str(snapshot.get('spatial_label')))} ({snapshot.get('spatial_score')})</li>
        <li>Historical probability: {escape(str(snapshot.get('historical_label')))} ({snapshot.get('historical_score')})</li>
        <li>Weighted probability: {escape(str(snapshot.get('weighted_label')))} ({snapshot.get('weighted_score')})</li>
      </ul>
      <h2>Confidence</h2>
      <p>Weighted confidence: {escape(str(snapshot.get('weighted_confidence_label')))} ({snapshot.get('weighted_confidence')})</p>
      <h2>Reason summary</h2>
      <p>{escape(str(snapshot.get('weighted_explanation')))}</p>
    </body></html>
    """


def render_event_page(payload: dict[str, Any]) -> str:
    if not payload:
        return "<html><body><p>Event not found.</p></body></html>"
    locations = "".join(f"<li>{escape(str(loc['location_name_raw']))}</li>" for loc in payload.get("locations", [])) or "<li>No locations</li>"
    return f"""
    <html><body>
      <h1>Event {payload.get('id')}</h1>
      <p>Type: {escape(str(payload.get('normalized_type')))}</p>
      <p>Started at: {escape(str(payload.get('started_at')))}</p>
      <h2>Locations</h2>
      <ul>{locations}</ul>
    </body></html>
    """
