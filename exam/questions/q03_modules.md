# Question 3: Modules

## 3.1: Demographics and calibration [30 marks]

##### 3.1.1: Your aim is to calibrate a model to the following data. [30 marks]

```py
import sciris as sc

# Define the target data
columns = ['years', 'births', 'deaths']
data = [[ 2000, 140660,  52520],
       [  2001, 137800,  54340],
       [  2002, 125060,  63180],
       [  2003, 148200,  58500],
       [  2004, 142740,  63180],
       [  2005, 150540,  57720],
       [  2006,  65780,  31200],
       [  2007,  62660,  30940],
       [  2008,  61360,  31980],
       [  2009,  62660,  30160],
       [  2010,  55640,  31980],
       [  2011,  73320,  34580],
       [  2012,  62140,  31200],
       [  2013,  69940,  32240],
       [  2014,  63440,  38220],
       [  2015,  64480,  29900],
       [  2016, 104000, 107900],
       [  2017, 104260, 102180],
       [  2018,  93860, 110760],
       [  2019,  91520, 104520],
       [  2020, 108420, 109720],
       [  2021,  95680,  98800],
       [  2022,  99320, 103220],
       [  2023,  99060, 105300],
       [  2024,  94120, 107120],
       [  2025, 104260, 104260],
       [  2026, 136760,  37440],
       [  2027, 140400,  33800],
       [  2028, 148200,  35100],
       [  2029, 158600,  40300],
       [  2030, 152620,  40560],
       [  2031, 163800,  45760],
       [  2032, 160160,  43160],
       [  2033, 167960,  38220],
       [  2034, 171600,  48100],
       [  2035, 176540,  47060],
       [  2036, 172900,  46020],
       [  2037, 181740,  47580],
       [  2038, 189800,  50960],
       [  2039, 193180,  52260],
       [  2040, 196560,  46540]]

df = sc.dataframe(data=data, columns=columns)
```

1. Create a simulation with births and deaths modules (no diseases or networks) with `years = [2000, 2010, 2020, 2030]` and `metadata = dict(data_cols=dict(year='year', value='value'))`.
2. Both births and deaths will have 4 parameters: the birth(/death) rate at each of the four control years.
3. Your simulation should have 10,000 agents, a total population size of 2.6 million, a start year of 2000, and stop year of 2040.
4. You can assume lower and upper bounds of 0 and 60 for both the birth rate and the death rate.
5. Use the `ss.Calibration` class. You can define the objective function however you want; however, a simple sum of absolute differences should suffice here, i.e. `sum(abs(data - model))`. Run for 500 trials.
6. Once the calibration is done, make a 2-panel figure for the births and deaths showing (a) the simulation with original parameters (assume birth rate = 30 and death rate = 10), (b) the best-fitting parameters, and (c) the data.
7. What are the best-fit parameter values for each of the parameters? Print as whole numbers (i.e. 0 decimal points).
8. What are the original and final objective function values?

## 3.2: Multiple diseases and interventions [36 marks]

##### 3.2.1: Create "fast" and "slow" versions of an SIS disease. The fast version should have beta = 0.1 per day and infection duration lognormally distributed with a mean of 7 days. The slow version should have beta = 0.02 per day, a mean duration of infection of 21 days. Both should have waning of 0.05 per day. Run a simulation with both diseases (using a random network, a timestep of a day, and run for 90 days; make sure you give the sim a label). Plot the results. Qualitatively describe the dynamics. [6 marks]

##### 3.2.2: Now add a "cross-immunity" connector. Here's how the connector should work: If a person became infected with the "slow" disease on the previous timestep, their "fast" disease immunity should be boosted by 1.0. If a person became infected with the "fast" disease on the previous timestep, their "slow" disease immunity should be boosted by 0.5. Run a new sim using this connector (with an appropriate label), then using MultiSim, plot the two run sims together. How does the connector change the dynamics? [7 marks]

##### 3.2.3: Not only do `fast` and `slow` diseases have cross-immunity, but scientists recently discovered that a vaccine administered while a person is infected with one of the diseases can significantly boost immunity. Implement a `test_and_vaccinate` intervention. The intervention should start on day 45. Testing coverage is 70% and the tests have a sensitivity of 90% (and specificity 100%). Vaccine coverage of people who test positive is 80%. People are vaccinated immediately (on the same timestep) as being diagnosed. People who are infected who receive the vaccine receive an immune boost of Normal(μ=5, σ=1) units (for both diseases, regardless of which one they are infected with). Run this sim, and plot all three sims together. Describe the dynamics. [23 marks]

