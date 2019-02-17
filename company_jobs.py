class CompanyJobs(object):
    def __init__(self, company, jobs_dict, wage):
        self.company = company
        self.jobs = {}
        for job_id, job_name in jobs_dict.items():
            self.jobs[job_name.lower()] = job_id
            self.jobs[job_id] = job_name
        self.wage = wage


    def get_id_by_name(self, _name):
        return self.jobs.get(_name.lower())

    def get_name_by_id(self, _id):
        return self.jobs.get(_id)

