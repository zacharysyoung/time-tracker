def print_hours_for_ken(invoice):
    print_str = invoice.company + '\n'
    grand_total = 0
    for job_id in sorted(invoice.job_ids.keys()):
        print_str += invoice.jobs.get_name_by_id(job_id) + ':\n'
        entries = invoice.job_ids[job_id]
        job_hours = 0
        for entry in entries:
            # like, Fr 02/01/19: 1.5
            dt = entry.dt
            day_date = '{} {}'.format(
                dt.strftime('%a')[:2], dt.strftime('%m/%d/%y')
            )
            print_str += '{}: {:.4g}\n'.format(day_date, entry.hours)
            job_hours += entry.hours
        print_str += '----\n'
        print_str += 'total: {:.5g}\n\n'.format(job_hours)

        grand_total += job_hours

    print_str += '----\n'
    print_str += 'total: {:.5g}\n\n'.format(grand_total)
    return print_str

def print_entries(invoice):
    print_str = ''
    for entry in invoice.entries:
        print_str += str(entry) + '\n'

    total = invoice.hours_total
    invoiced = invoice.invoiced_dt
    payment_due = invoice.payment_dt
    gross_pay = total * invoice.jobs.wage

    print_str += '\nTotal: {} | Invoiced: {} | Payment due: {} | Gross $: {}'.format(
        total, invoiced, payment_due, gross_pay
        )
    print_str += '\n----\n'
    return print_str

def write_invoice_report(invoice, path):
    with open(path, 'w') as f:
        f.write(print_hours_for_ken(invoice))
        f.write(print_entries(invoice))

def parse_entries_from_note(note_data, jobs):
    from time_entry import TimeEntry
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

        if jobs.get_name_by_id(id_or_name):
            return id_or_name

        job_id = jobs.get_id_by_name(id_or_name)
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
