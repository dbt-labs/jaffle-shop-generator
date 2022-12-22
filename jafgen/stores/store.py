class Store(object):
    def __init__(self, store_id, name, base_popularity, hours_of_operation, opened_date, tax_rate):
        self.store_id = store_id
        self.name = name
        self.base_popularity = base_popularity
        self.hours_of_operation = hours_of_operation
        self.opened_date = opened_date
        self.tax_rate = tax_rate

    def p_buy(self, date):
        date_effect = date.get_effect()
        return self.base_popularity * date_effect

    def minutes_open(self, date):
        return self.hours_of_operation.minutes_open(date)

    def iter_minutes_open(self, date):
        yield from self.hours_of_operation.iter_minutes(date)

    def is_open(self, date):
        return date.date >= self.opened_date.date

    def is_open_at(self, date):
        return self.hours_of_operation.is_open(date)

    def days_since_open(self, date):
        return date.date_index - self.opened_date.date_index

    def opens_at(self, date):
        return self.hours_of_operation.opens_at(date)

    def closes_at(self, date):
        return self.hours_of_operation.closes_at(date)

    def to_dict(self):
        return {
            "id": self.store_id,
            "name": self.name,
            "opened_at": self.opened_date.date.isoformat(),
            "tax_rate": self.tax_rate,
        }
