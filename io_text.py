import ConfigParser

class IoTxt(object):
    @classmethod
    def read_company_jobs(cls, path, company_name):
        config = ConfigParser.ConfigParser()
        with open(path, 'r') as f:
                config.readfp(f)

        return dict(config.items(company_name))

    @classmethod
    def write_invoice(cls, path, invoice):
        f = open(path, 'w')

        f.write(invoice.company + '\n')
        grand_total = 0
        for job_id in sorted(invoice.job_ids.keys()):
            f.write(invoice.jobs.get_name_by_id(job_id) + ':\n')
            entries = invoice.job_ids[job_id]
            for entry in entries:
                # like, Fr 02/01/19: 1.5
                dt = entry.dt
                day_date = '{} {}'.format(
                    dt.strftime('%a')[:2], dt.strftime('%m/%d/%y')
                )
                f.write('{}: {:.4g}\n'.format(day_date, entry.hours))
            f.write('----\n')
            total = invoice.total_hours
            f.write('total: {:.5g}\n\n'.format(total))

            grand_total += total

        f.write('----\n')
        f.write('total: {:.5g}\n\n'.format(grand_total))

        for entry in invoice.entries:
            f.write(str(entry) + '\n')

        total = invoice.total_hours
        invoiced = invoice.invoiced_dt
        payment_due = invoice.payment_dt
        gross_pay = total * invoice.jobs.wage

        f.write('\nTotal: {} | Invoiced: {} | Payment due: {} | Gross $: {}'.format(total, invoiced, payment_due, gross_pay))
        f.write('\n----\n')

        
        f.close()
        

