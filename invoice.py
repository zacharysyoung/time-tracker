import datetime

from collections import defaultdict

from time_entry import TimeEntry

class Invoice(object):
    def __init__(self, entries, payment_date, config=None):
        for i in range(len(entries) - 1, -1, -1):
            if i > 0 and entries[i].company != entries[i - 1].company:
                raise ValueError('Found entries with different companies: %s and %s' % (entries[i].company, entries[i - 1].company))

            if not entries[i].can_be_invoiced():
                del(entries[i])

        self.entries = sorted(entries, key=lambda x: x.dt)
        self.job_ids = defaultdict(list)
        for entry in self.entries:
            self.job_ids[entry.job].append(entry)

        self.scheduled_payment_date = payment_date
        self.hours_total  = TimeEntry.get_hours_total(self.entries)
        self.company = self.entries[0].company
        self.datetime_invoiced = None
        self.datetime_paid = None
        self.sent = False

        self.config = config

    def print_txt(self, config=None):

        if not config:
            config = self.config

        print_str = self.company + '\n'
        grand_total = 0
        for job_id in sorted(self.job_ids.keys()):
            print_str += config.get_name_by_id(job_id) + ':\n'
            entries = self.job_ids[job_id]
            for entry in entries:
                # like, Fr 02/01/19: 1.5
                dt = entry.dt
                day_date = '{} {}'.format(
                    dt.strftime('%a')[:2], dt.strftime('%m/%d/%y')
                )
                print_str += '{}: {:.4g}\n'.format(day_date, entry.hours)
            print_str += '----\n'
            total = TimeEntry.get_hours_total(entries)
            print_str += 'total: {:.5g}\n\n'.format(total)

            grand_total += total

        print_str += '----\n'
        print_str += 'total: {:.5g}\n\n'.format(grand_total)
        return print_str

    def send(self):
        now = datetime.datetime.now()
        for entry in self.entries:
            entry.invoiced = True
            entry.datetime_invoiced = now
        self.datetime_invoiced = now
        self.sent = True

    def print_entries(self):
        print_str = ''
        for entry in self.entries:
            print_str += str(entry) + '\n'

        total = TimeEntry.get_hours_total(self.entries)
        invoiced = self.datetime_invoiced
        payment_due = self.scheduled_payment_date

        print_str += '\nTotal: {} | Invoiced: {} | Payment due: {}'.format(
            total, invoiced, payment_due
            )
        print_str += '\n----\n'
        return print_str

    def write_file(self, path, mode='w+b'):
        with open(path, mode) as f:
            f.write(self.print_txt())
            f.write(self.print_entries())
