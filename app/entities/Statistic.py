# coding=utf-8
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.entities.activity import Activity
from app.entities.activity_type import ActivityType
from app.entities.country import Country
from app.entities.entity import Entity, Base
from app.entities.hike_relations import HikeRelation
from app.entities.location import Location
from app.entities.location_activity import LocationActivity
from app.entities.region import Region
from app.utils.helpers import sort_dict


def count_entries(session, cls):
    return session.query(cls).count()


def update_popularity_on_location_activity(session):
    result = session.query(LocationActivity).join(Location).all()
    countries = {}
    regions = {}
    for r in result:
        if r.locations.region.country.abbreviation in countries.keys():
            countries[r.locations.region.country.id] += 1
        else:
            countries.update({r.locations.region.country.id: 1})

        if r.locations.region.name in regions.keys():
            regions[r.locations.region.id] += 1
        else:
            regions.update({r.locations.region.id: 1})
    countries = sort_dict(countries.items())
    regions = sort_dict(regions.items())

    return next(iter(countries)) if len(countries) > 0 else None, next(iter(regions)) if len(regions) > 0 else None


def update_popularity_on_activity(session):
    result = session.query(Activity).join(ActivityType).all()
    act_types = {}
    for r in result:
        if r.activity_type.name in act_types.keys():
            act_types[r.activity_type.id] += 1
        else:
            act_types.update({r.activity_type.id: 1})
    act_types = sort_dict(act_types.items())

    return next(iter(act_types)) if len(act_types) > 0 else None


def update_popularity_on_hike_relation(session):
    result = session.query(HikeRelation).join(Activity).all()
    activities = {}
    for r in result:
        if r.activity.name in activities.keys():
            activities[r.activity.id] += 1
        else:
            activities.update({r.activity.id: 1})
    activities = sort_dict(activities.items())

    return next(iter(activities)) if len(activities) > 0 else None


dict_class_no_attribute = {
    Activity: 'no_activities',
    Country: 'no_countries',
    Region: 'no_regions',
    Location: 'no_locations'
}

dict_class_pop_attribute = {
    Activity: 'pop_activity_id',
    Country: 'pop_country_id',
    Region: 'pop_region_id',
    ActivityType: 'pop_activity_type_id'
}


class Statistic(Entity, Base):
    __tablename__ = 'statistic'

    no_activities = Column(Integer, nullable=False)
    no_countries = Column(Integer, nullable=False)
    no_regions = Column(Integer, nullable=False)
    no_locations = Column(Integer, nullable=False)
    pop_country_id = Column(Integer, ForeignKey('countries.id'))
    pop_country = relationship('Country', foreign_keys=pop_country_id)
    pop_region_id = Column(Integer, ForeignKey('regions.id'))
    pop_region = relationship('Region', foreign_keys=pop_region_id)
    pop_activity_type_id = Column(Integer, ForeignKey('activity_types.id'))
    pop_activity_type = relationship('ActivityType', foreign_keys=pop_activity_type_id)
    pop_activity_id = Column(Integer, ForeignKey('activities.id'))
    pop_activity = relationship('Activity', foreign_keys=pop_activity_id)

    def __init__(self):
        Entity.__init__(self)
        self.no_activities = 0
        self.no_countries = 0
        self.no_regions = 0
        self.no_locations = 0
        self.pop_country_id = None
        self.pop_region_id = None
        self.pop_activity_type_id = None
        self.pop_activity_id = None
        self.last_updated_by = 'System'

    def create(self, session):
        stat_exists = session.query(self.__class__).count() > 0

        if stat_exists:
            raise RuntimeError('Statistic instance already exists, call instance() instance')
        else:

            session.add(self)
            session.commit()

            for cls in [Activity, Country, Region, Location]:
                self.update_number(session, cls, False)
            for cls in [LocationActivity, Activity, HikeRelation]:
                self.update_popularity(session, cls, False)

        return self

    def update(self, session, **kwargs):
        self.updated_at = datetime.now()
        self.last_updated_by = 'System'

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        session.add(self)
        session.commit()

    def update_number(self, session, cls, stop_session=True):
        no = count_entries(session, cls)
        self.update(session, **{dict_class_no_attribute[cls]: no})
        if stop_session:
            session.expunge_all()
            session.close()

    def update_popularity(self, session, cls, stop_session=True):
        if cls == LocationActivity:
            pop_country, pop_region = update_popularity_on_location_activity(session)
            self.update(session, **{dict_class_pop_attribute[Country]: pop_country,
                                    dict_class_pop_attribute[Region]: pop_region})
        elif cls == Activity:
            pop_activity_type = update_popularity_on_activity(session)
            self.update(session, **{dict_class_pop_attribute[ActivityType]: pop_activity_type})

        elif cls == HikeRelation:
            pop_activity = update_popularity_on_hike_relation(session)
            self.update(session, **{dict_class_pop_attribute[Activity]: pop_activity})

        if stop_session:
            session.expunge_all()
            session.close()

    def _increase(self, session, attr):
        if attr not in ['no_activities', 'no_countries', 'no_regions', 'no_locations']:
            raise AttributeError("Attribute cannot be increased")
        elif not hasattr(self, attr):
            raise AttributeError("Attribute does not exist")
        else:
            setattr(self, attr, getattr(self, attr) + 1)
            self.update(session)

    def update_countries(self, session):
        self.count(session, 'no_countries')

    @classmethod
    def instance(cls, session):
        # check whether Statistic already exists
        if session.query(cls).count() == 0:
            raise RuntimeError('Statistic does not exist, initialize Statistic first and call create()')
        else:
            return session.query(cls).get(1)
