import numpy as np
from datetime import timedelta

class OGI_crew:
    def __init__ (self, state, parameters, config, timeseries, deployment_days, id):
        '''
        Constructs an individual OGI crew based on defined configuration.
        '''
        self.state = state
        self.parameters = parameters
        self.config = config
        self.timeseries = timeseries
        self.deployment_days = deployment_days
        self.crewstate = {'id': id}     # Crewstate is unique to this agent
        self.crewstate['truck'] = np.random.choice (self.config['truck_types'])
        self.crewstate['lat'] = 0.0
        self.crewstate['lon'] = 0.0
        return

    def work_a_day (self):
        '''
        Go to work and find the leaks for a given day
        '''
                                                              # Reset well count
        self.state['t'].current_date = self.state['t'].current_date.replace(hour = 8)              # Set start of work day
        while self.state['t'].current_date.hour < 18:
            facility_ID, found_site, site = self.choose_site ()
            if not found_site:
                break                                   # Break out if no site can be found
            self.visit_site (facility_ID, site)

        return


    def choose_site (self):
        '''
        Choose a site to survey.

        '''
            
        # Sort all sites based on a neglect ranking
        self.state['sites'] = sorted(self.state['sites'], key=lambda k: k['t_since_last_LDAR_OGI'], reverse = True)

        facility_ID = None                                  # The facility ID gets assigned if a site is found
        found_site = False                                  # The found site flag is updated if a site is found

        # Then, starting with the most neglected site, check if conditions are suitable for LDAR
        for site in self.state['sites']:

            # If the site hasn't been attempted yet today
            if site['attempted_today_OGI?'] == False:
            
                # If the site is 'unripened' (i.e. hasn't met the minimum interval set out in the LDAR regulations/policy), break out - no LDAR today
                if site['t_since_last_LDAR_OGI'] < self.parameters['methods']['M21']['min_interval']:
                    self.state['t'].current_date = self.state['t'].current_date.replace(hour = 23)
                    break
    
                # Else if site-specific required visits have not been met for the year
                elif site['surveys_done_this_year_OGI'] < int(site['required_surveys_OGI']):
    
                    # Check the weather for that site
                    if self.deployment_days[site['lon_index'], site['lat_index'], self.state['t'].current_timestep] == True:
                    
                        # The site passes all the tests! Choose it!
                        facility_ID = site['facility_ID']   
                        found_site = True
    
                        # Update site
                        site['surveys_conducted_OGI'] += 1
                        site['surveys_done_this_year_OGI'] += 1
                        site['t_since_last_LDAR_OGI'] = 0
                        break
                                            
                    else:
                        site['attempted_today_OGI?'] = True
                        self.timeseries['wells_skipped_weather'][self.state['t'].current_timestep] += 1

        return (facility_ID, found_site, site)

    def visit_site (self, facility_ID, site):
        '''
        Look for leaks at the chosen site.
        '''

        # Identify all the leaks at a site
        self.leaks_present = []
        for leak in self.state['leaks']:
            if leak['facility_ID'] == facility_ID:
                if leak['status'] == 'active':
                    self.leaks_present.append(leak)

        # Add these leaks to the 'tag pool'
        for leak in self.leaks_present:
            leak['date_found'] = self.state['t'].current_date
            leak['found_by_company'] = 'OGI_company'
            leak['found_by_crew'] = self.crewstate['id']
            self.state['tags'].append(leak)

        self.state['t'].current_date += timedelta(minutes = int(site['OGI_time']))


        self.random_disaster ()         # See if there's a disaster
        return


    def random_disaster (self):
        '''
        random disasters
        '''

        if np.random.random() > 0.9999:
            disaster = np.random.choice (['car crash', 'OGI camera failure', 'tire blowout'])
            print ('OGI crew ' + str (self.crewstate['id']) + ' with a ' + \
                    self.crewstate['truck'] + ' truck had a ' + disaster)

            # no more wells today
            self.state['t'].current_date = self.state['t'].current_date.replace(hour = 23)
        return
