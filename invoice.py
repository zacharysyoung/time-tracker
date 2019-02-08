import datetime

from collections import defaultdict

from time_entry import TimeEntry

class Invoice(object):
    def __init__(self, entries, payment_date):
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

    def print_txt(self, config):
        print_str = self.company + '\n'
        grand_total = 0
        for job_id in sorted(self.job_ids.keys()):
            print_str += config.get_name_by_id(job_id) + ':\n'
            entries = self.job_ids[job_id]
            for entry in entries:
                dt = entry.dt
                print_str += '{}: {:.4g}\n'.format(dt.strftime('%a')[:2] + ' ' + dt.strftime('%m/%d/%y'), entry.hours)
            print_str += '----\n'
            print_str += 'total: {:.5g}\n\n'.format(TimeEntry.get_hours_total(entries))

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
