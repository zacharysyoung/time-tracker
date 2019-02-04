class TimeEntry(object):
    @classmethod
    def add(cls, *entries):
        total = 0
        for entry in entries:
            total += entry.hours
        return total

    @classmethod
    def get_uninvoiced(cls, *entries):
        _entries = []
        for entry in entries:
            if entry.invoiced is False and entry.billable is True:
                _entries.append(entry)
        return _entries

    @classmethod
    def query(cls, entries, company=None):
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

    def  __repr__(self):
        return 'TimeEntry(%s, %s, %s, %s, %s, %s)' % (
            self.hours,
            self.dt,
            self.message,
            self.company,
            self.job,
            self.billable
        )
    
