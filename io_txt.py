import os
import cPickle


def get_report_name(invoice):
    return '{:%Y%m%d}_{:%Y%m%d}_{}'.format(
        invoice.payperiod_start, invoice.payperiod_end, invoice.company)

def get_invoice_path(invoice):
    return 'io/fs/invoices/{}.pkl'.format(invoice.id)

def get_report_path(invoice):
    return 'io/fs/reports/{}.txt'.format(get_report_name(invoice))

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

def open_invoice(path):
    return unpickle(path)

def write_invoice(invoice):
    path = get_invoice_path(invoice)
    if os.path.exists(path):
        raise IOError(1024, 'File already exists: %s' % path)
    pickle(invoice, path)

def write_report(invoice):
    path = get_report_path(invoice)
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

    if not note_data.getvalue().strip():
        raise ValueError('no data in note_data')
    note_data.seek(0)

    reader = csv.reader(note_data, delimiter=',', quotechar='"')
    entries = []
    for row in reader:
        if not row:
            continue

        _assert_field_count(row, 5)

        entries.append(TimeEntry(
            cast_float(row[0]),
            cast_date(row[1]),
            _unicode(row[2]),
            _unicode(row[3]),
            _job_id(row[4])
        )
        )

    return entries

def get_entry_name(entry):
    return str(entry.id)

def get_entry_path(entry):
    return 'io/fs/entries/' + get_entry_name(entry) + '.pkl'

def open_entry(path):
    return unpickle(path)

def write_entry(entry):
    path = get_entry_path(entry)
    if os.path.exists(path):
        raise IOError(1024, 'File already exists: %s' % path)
    pickle(entry, path)

def unpickle(fname):
    with open(fname, 'r+b') as f:
        return cPickle.load(f)

def pickle(obj, fname):
    with open(fname, 'w+b') as f:
        return cPickle.dump(obj, f, protocol=-1)
