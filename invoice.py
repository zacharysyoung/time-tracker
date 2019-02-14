import datetime

from collections import defaultdict

from time_entry import TimeEntry

class Invoice(object):
    def __init__(self, entries, payment_dt, pay_period, jobs):
        self.company = jobs.company

        for i in range(len(entries) - 1, -1, -1):
            if entries[i].company != self.company:
                raise ValueError(
                    'Entry with different company: %s and %s' % (
                        repr(entries[i]), self.company))

            if not entries[i].can_be_invoiced():
                del(entries[i])

        self.entries = sorted(entries, key=lambda x: x.dt)
        self.job_ids = defaultdict(list)
        for entry in self.entries:
            self.job_ids[entry.job].append(entry)

        self.hours_total  = TimeEntry.get_hours_total(self.entries)
        self.invoiced_dt = None
        self.payment_dt = payment_dt
        self.paid_dt = None
        self.sent = False

        self.payperiod_start = pay_period[0]
        self.payperiod_end = pay_period[1]
        self.jobs = jobs

    def print_txt(self):
        print_str = self.company + '\n'
        grand_total = 0
        for job_id in sorted(self.job_ids.keys()):
            print_str += self.jobs.get_name_by_id(job_id) + ':\n'
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
        total = 0
        for entry in self.entries:
            entry.invoiced = True
            entry.invoiced_dt = now
            total += entry.hours
        self.invoiced_dt = now
        self.sent = True
        self.total_hours = total

    def print_entries(self):
        print_str = ''
        for entry in self.entries:
            print_str += str(entry) + '\n'

        total = TimeEntry.get_hours_total(self.entries)
        invoiced = self.invoiced_dt
        payment_due = self.payment_dt
        gross_pay = total * self.jobs.wage

        print_str += '\nTotal: {} | Invoiced: {} | Payment due: {} | Gross $: {}'.format(
            total, invoiced, payment_due, gross_pay
            )
        print_str += '\n----\n'
        return print_str

    def write_file(self, path, mode='w+b'):
        with open(path, mode) as f:
            f.write(self.print_txt())
            f.write(self.print_entries())
