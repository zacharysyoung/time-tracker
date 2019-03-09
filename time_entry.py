import uuid

class TimeEntry(object):
    @classmethod
    def get_hours_total(cls, entries):
        hours_total = 0
        for entry in entries:
            hours_total += entry.hours
        return hours_total

    @classmethod
    def query(cls, entries, company):
        """This only ever seems to be called right before making an invoice,
            so maybe this belongs in invoice.py.
        """
        _entries = []
        for entry in entries:
            if company and entry.company == company:
                _entries.append(entry)
        return _entries

    def __init__(self, hours, dt, message, company, job, billable=True):
        self.hours = hours
        self.dt = dt
        self.message = message
        self.billable = billable
        self.invoiced = False
        self.company = company
        self.job = job
        self.id = uuid.uuid1().hex

    def __eq__(self, other):
        return other.id is self.id

    def __ne__(self, other):
        return other.id is self.id

    def can_be_invoiced(self):
        return self.billable and not self.invoiced

    def  __repr__(self):
        return 'TimeEntry(%s, %s, %s, %s, %s, %s)' % (
            self.hours,
            self.dt,
            self.message,
            self.company,
            self.job,
            self.billable
        )

    def __str__(self):
        return '| ' + ' | '.join([
            '%g' % self.hours,
            self.dt.strftime('%m/%d/%y'),
            self.message,
            self.company,
            self.job
        ]) + ' |'
