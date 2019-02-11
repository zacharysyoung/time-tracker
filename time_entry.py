class TimeEntry(object):
    @classmethod
    def get_hours_total(cls, entries):
        hours_total = 0
        for entry in entries:
            hours_total += entry.hours
        return hours_total

    @classmethod
    def get_uninvoiced(cls, entries):
        _entries = []
        for entry in entries:
            if entry.can_be_invoiced():
                _entries.append(entry)
        return _entries

    @classmethod
    def parse_note(cls, note_data, config):
        def _assert_field_count(row, field_count):
            assert len(row) == field_count, \
                'Expected %s field(s) in row, got %d: %s' % (field_count, len(row), row)

        def cast_date(s):
            if not s:
                return None

            mo, day, yr = map(int, s.split('/'))
            return datetime.datetime(2000 + yr, mo, day)


        def cast_float(s):
            if not s:
                return None
            return float(s)


        def cast_int(s):
            if not s:
                return None
            return int(s)


        def _unicode(s):
            if not s:
                return None

            return unicode(s, 'utf-8')

        def _job_id(s):
            if not s:
                return None

            id_or_name = _unicode(s)

            # Use value as id for name, and return id
            if config.get_name_by_id(id_or_name):
                return id_or_name

            # Use value as name for id
            job_id = config.get_id_by_name(id_or_name)
            if job_id:
                return job_id

            return None

        import csv
        import datetime

        reader = csv.reader(note_data, delimiter=',', quotechar='"')
        entries = []
        for row in reader:
            if not row:
                continue

            entries.append(TimeEntry(
                cast_float(row[0]),
                cast_date(row[1]),
                _unicode(row[2]),
                _unicode(row[3]),
                _job_id(row[4])
            )
            )
        return entries

    @classmethod
    def query(cls, entries, company, job=None):
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

    def __eq__(self, other):
        return self.hours == other.hours and \
               self.dt == other.dt and \
               self.message == other.message and \
               self.billable == other.billable and \
               self.invoiced == other.invoiced and \
               self.company == other.company and \
               self.job == other.job

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
