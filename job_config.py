import ConfigParser


class JobConfig(object):
    def __init__(self, config_data, company):
        config = ConfigParser.ConfigParser()
        config.readfp(config_data)

        self.jobs = {}
        for job_id, job_name in config.items(company):
            self.jobs[job_name] = job_id
            self.jobs[job_id] = job_name


    def get_id_by_name(self, _name):
        return self.jobs[_name]

    def get_name_by_id(self, _id):
        return self.jobs[_id]

    @classmethod
    def get_jobs_from_ini(cls, ini_data=None):
        """
        From id: Name to {name: id, id: id}, so that a search by name or
        or id always returns id
        """

        if ini_data:
            pass
        else:
            with open('jobs.ini', 'r') as f:
                config.readfp(f)




    def _job(s, company):
        if not s:
            return None

        s = _unicode(s)
        return _jobs[company][s]


