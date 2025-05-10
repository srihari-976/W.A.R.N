from backend.db import db, Table, Column, Integer, ForeignKey

# Association table for alerts and events
alert_events = Table(
    'alert_events',
    db.metadata,
    Column('alert_id', Integer, ForeignKey('alerts.id'), primary_key=True),
    Column('event_id', Integer, ForeignKey('security_events.id'), primary_key=True)
) 