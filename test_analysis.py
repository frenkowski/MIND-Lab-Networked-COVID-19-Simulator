from collections import Counter
import igraph as ig
import statistics as stat
from pathlib import Path
import matplotlib.pyplot as plt

# used to run simulation
from ctns.contact_network_simulator import run_simulation

def compute_network_history(nets):
	"""
    Compute the dayly counter of Susceptibile, Exposed, Infectedm, Recovered, Dead, Quarantine, Tested, Positive.
    Return dictionary with keys S, E, I, R, D, Q, tot, tested, positive and values list of dayly counter according to
    the keys.
    
    Parameters
    ----------
    nets: list of ig.Graph()
        List of dayly igraph objects

    Return
    ------
    network_history: dictionary of agent status and tests
    	Dictionary keys: 	S, E, I, R, D, Q, tot, tested, positive 
				   values:	list of dayly counter of key
    """
	network_history = {}
	network_history['S'] = list()
	network_history['E'] = list()
	network_history['I'] = list()
	network_history['R'] = list()
	network_history['D'] = list()
	network_history['quarantined'] = list()
	network_history['positive'] = list()
	network_history['tested'] = list()
	network_history['total'] = list()

	for day in range(len(nets)):
		G = nets[day]

		network_report = Counter(G.vs["agent_status"])

		tested = 0
		quarantined = 0
		positive = 0
		
		for node in G.vs:
			if node["test_result"] != -1:
				tested += 1
			if node["test_result"] == 1:
				positive += 1
			if node["quarantine"] != 0:
				quarantined += 1

		tot = sum(network_report.values())
		network_report['quarantined'] = quarantined
		network_report['positive'] = positive
		network_report['tested'] = tested


		network_history['S'].append(network_report['S'])
		network_history['E'].append(network_report['E'])
		network_history['I'].append(network_report['I'])
		network_history['R'].append(network_report['R'])
		network_history['D'].append(network_report['D'])
		network_history['quarantined'].append(network_report['quarantined'])
		network_history['positive'].append(network_report['positive'])
		network_history['tested'].append(network_report['tested'])
		network_history['total'].append(tot)

	return network_history


def plot_network_info(nets, sim_name):
	#To-do
	print(sim_name)
	print("Simulation days ", len(nets))
	print("Number of nodes: ", len(nets[0].vs))
	
                


def plot_simulation(network_history, sim_name):
	"""
    Plot simulation trends and statistics of infected people.
    Save the results plot in the folder.
    
    Parameters
    ----------
    network_history: dictionary of agent status and tests
    	Dictionary keys: 	S, E, I, R, D, Q, tot, tested, positive 
				   values:	list of dayly counter of key

	sim_name: simulation name for saving the images

    Return
    ------
    None
    	Save the results on file.
    """
	
	colors = {'S':'#0000ff', 'E':'#ffa300', 'I':'#ff0000', 'D':'#000000', 'R':'#00ff00'}
	days = list(range(len(network_history['S'])))
	last_day = len(days) -1

	plt.figsize=(8, 6)
	plt.subplot(211)#, 
	plt.plot(days, network_history['S'], label = 'S', color = colors['S'])
	plt.plot(days, network_history['E'], label =  'E', color = colors['E'])
	plt.plot(days, network_history['I'], label =  'I', color = colors['I'])
	plt.plot(days, network_history['R'], label =  'R', color = colors['R'])
	plt.plot(days, network_history['D'], label = 'D', color = colors['D'])
	plt.title('Simulation results')
	plt.legend()
	
	
	
	# plot testing results
	plt.subplot(212)
	plt.plot(days, network_history['quarantined'], label =  'quarantined')
	plt.plot(days, network_history['tested'], label = 'tested')
	plt.plot(days, network_history['positive'], label = 'positive')
	plt.plot(days, network_history['total'], label = 'total')
	plt.legend()
	plt.tight_layout()
	path_save = Path('analysis/simulation_results_{}.png'.format(sim_name))
	plt.savefig(path_save, dpi = 200, optimize = True)
	#plt.show()
	plt.close()


	# plot all infected people
	
	total_infeted = network_history['total'][last_day] - network_history['S'][last_day]
	total_tested = network_history['tested'][last_day]

	print("Number of total infected people {}".format(total_infeted))

	
	total_positive = sum(network_history['positive'])
	print("Number of total positive test {}".format(total_positive))
	
	#TO_DO
	total_quarantine = network_history['quarantined'][0]
	for day in range(1, len(network_history['quarantined'])):
		new_Q = network_history['quarantined'][day] - network_history['quarantined'][day-1]
		total_quarantine += new_Q
	
	
	fig = plt.figure(figsize=(8, 6))
	ax = plt.axes()

	width = 0.1
	plt.bar(0, total_infeted, width, label = "All infected people")
	plt.bar(width, total_tested, width = width, label = "All tested people")
	plt.bar(width*2, total_positive, width = width, label = "All positive test")
	plt.bar(width*3, total_quarantine, width = width, label = "All quarantined people")
	
	x_range = ax.axes.get_xlim()
	plt.hlines(network_history['total'][0], x_range[0], x_range[1], label = "All people", linestyles = 'dashed', linewidth = 1)
	
	plt.title('All infected people')
	ax.axes.set_xlim(x_range)
	ax.axes.get_xaxis().set_visible(False)
	plt.tight_layout()
	plt.legend()
	path_save = Path('analysis/{}_infected.png'.format(sim_name))
	plt.savefig(path_save, dpi = 200, optimize = True)
	plt.show()
	plt.close()


def plot_degree_dist(G, node_sociability = None, edge_category = None, title = None, sim_name = ""):
    """
    Print degree probability distribution of the network.
    node_sociability and edge_category can be used to filter only certain types of
    nodes and edges
    
    Parameters
    ----------
    G: ig.Graph()
        The contact network

    node_sociability: string
        Consider only nodes that have sociability == node_sociability

    edge_category: string
        Consider only edges that have category == edge_category

    title: string
        The title of the plot

    sim_name: string
        The name of current simulation to plot

    Return
    ------
    None
    	Save the results on file.

    """
    plt.figure(figsize = (8, 6))
    if edge_category != None:
        G = G.copy()
        toRemove = []
        for edge in G.es:
            if edge["category"] != edge_category:
                toRemove.append(edge.index)
        G.delete_edges(toRemove)


    if node_sociability == None:
        degs = G.degree()
    else:
        selected_nodes = list()
        for node in G.vs:
            if node['sociability'] == node_sociability:
                selected_nodes.append(node)
        degs = G.degree(selected_nodes) 

    counted_degs = Counter(degs)

    for key in counted_degs.keys():
        counted_degs[key] = counted_degs[key] / len(G.vs())
        plt.bar(key, counted_degs[key], color ='tab:blue')#,marker = '.', color = "red", s = 10)

    plt.xticks(fontsize = 12)
    plt.yticks(fontsize = 12)
    
    #fix x-ticks
    #xint = []
    #locs, labels = plt.xticks()
    #for each in locs:
    #    xint.append(int(each))
    #plt.xticks(xint)

    plt.xlabel("Degree", fontsize = 15)
    plt.ylabel("Probability", fontsize = 15)
    if title == None:
        plt.title("Degree distribution", fontsize = 20)
    else:
        plt.title(title, fontsize = 20)
    plt.tight_layout()
    path_save = Path('analysis/{}_{}.png'.format(title, sim_name))
    plt.savefig(path_save, dpi = 200, optimize = True)
    #plt.show()
    plt.close()  


# Print degree distribution
def print_degree_summary(G, sim_name):

    """
    Print degree probability distribution dummary of the network.
    
    Parameters
    ----------
    G: ig.Graph()
        The contact network

    sim_name: string
        The name of current simulation to plot

    Return
    ------
    None
    	Save the results on file.
    """
    plot_degree_dist(G, title = "Degree distribution", sim_name = sim_name)
    plot_degree_dist(G, node_sociability = "low", title = "Degree distribution low sociability", sim_name = sim_name)
    plot_degree_dist(G, node_sociability = "medium", title = "Degree distribution medium sociability", sim_name = sim_name)
    plot_degree_dist(G, node_sociability = "high", title = "Degree distribution high sociability", sim_name = sim_name)

    plot_degree_dist(G, edge_category = "family_contacts", title = "Degree distribution family contacts", sim_name = sim_name)
    plot_degree_dist(G, edge_category = "frequent_contacts", title = "Degree distribution frequent contacts", sim_name = sim_name)
    plot_degree_dist(G, edge_category = "occasional_contacts", title = "Degree distribution occasional contacts", sim_name = sim_name)
    plot_degree_dist(G, edge_category = "random_contacts", title = "Degree distribution random contacts", sim_name = sim_name)




def plot_comparison_infected_dead(list_nets_history, name_list, color_list):
	"""
    Plot comparison of different simulation to investigate the differences and the effect of different parameters.
    
    Parameters
    ----------
    list_nets_history: list of dictionary of agent status and tests
    	Dictionary keys: 	S, E, I, R, D, Q, tot, tested, positive 
				   values:	list of dayly counter of key

	name_list: list of simulation name to compare and for saving the images

	color_list: list of colors for plotting simulation results

    Return
    ------
    None
    	Save the results on file.
    """


	plt.figsize=(8, 6)
	i = 0
	plt.subplot(211)
	for network_history in list_nets_history:
		days = list(range(len(network_history['S'])))
		infected = [network_history['I'][i] + network_history['E'][i] for i in range(len(network_history['I']))]
		plt.plot(days, infected, label = "Infected " + name_list[i], color = color_list[i])
		i+=1
		

	plt.title('Comparison simulation results')
	plt.legend()
	
	
	# plot dead results
	i = 0
	plt.subplot(212)
	for network_history in  list_nets_history:
		days = list(range(len(network_history['S'])))
		plt.plot(days, network_history['D'], label = "Dead " + name_list[i], color = color_list[i])
		i+=1
		
	plt.legend()
	plt.tight_layout()
	path_save = Path('analysis/comparison_results.png')
	plt.savefig(path_save, dpi = 200, optimize = True)
	#plt.show()
	plt.close()
		

def plot_pie_chart_summary(list_nets_history, name_list):

	"""
    Plot pie charts of Susceptibile, Recovered and dead at the end of simulation
    
    Parameters
    ----------
    list_nets_history: list of dictionary of agent status and tests
    	Dictionary keys: 	S, E, I, R, D, Q, tot, tested, positive 
				   values:	list of dayly counter of key

	name_list: list of simulation name to compare and for saving the images


    Return
    ------
    None
    	Save the results on file.
    """

	colors = {'S':'#0000ff', 'E':'#ffa300', 'I':'#ff0000', 'D':'#000000', 'R':'#00ff00'}
	labels = ['S', 'R', 'D']
	for i in range(len(name_list)):
		network_history = list_nets_history[i]
	
		last_day = len(network_history['S']) - 1
		n_of_nodes =  network_history['total'][last_day]

		s = network_history['S'][last_day] / n_of_nodes
		r = network_history['R'][last_day] / n_of_nodes
		d = network_history['D'][last_day] / n_of_nodes

		sizes = [s, r, d]
		explode = (0.25, 0, 0)  
		list_colors = [colors['S'], colors['R'], colors['D']]

		fig1, ax1 = plt.subplots()
		ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
		        shadow=True, startangle=90, colors = list_colors)
		ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
		plt.title('Population summary at the end of simulation')
		plt.tight_layout()
		path_save = Path('analysis/Pie_chart_{}.png'.format(name_list[i]))
		plt.savefig(path_save, dpi = 200, optimize = True)
		#plt.show()
		plt.close()






if __name__ == "__main__":

	n_of_families = [500, 500, 500]
	use_steps = [True, True, True]
	number_of_steps = [150, 150, 150]
	incubation_days = [5, 5, 5]
	infection_duration =	[21, 21, 21]  
	initial_day_restriction =	[0, 25, 25]
	restriction_duration = [0, 21, 21]
	social_distance_strictness = [0, 4, 2]
	restriction_decreasing = [False, True, True]
	n_initial_infected_nodes = [5, 5, 5]
	R_0 = [2.9, 2.9, 2.9]
	n_test = [0, 0, 5]
	policy_test = ["Random", "Random", "Random"]
	contact_tracking_efficiency = [0, 0, 0.7]
    
    #fixed ?
	dump = False
	path = None
	seed = 42
	use_random_seed = True
	
    # add color and name list according to the number of simulation to plot!
	name_list  = ['sim1','sim2', 'sim3']
	color_list = ["blue", "red", 'black']

	list_nets_history = list()
	
	for i in range(len(name_list)):
		result_nets = run_simulation(use_steps = use_steps[i],
									 number_of_steps= number_of_steps[i],
									 incubation_days = incubation_days[i],
									 infection_duration = infection_duration[i],
									 initial_day_restriction = initial_day_restriction[i],
									 restriction_duration = restriction_duration[i],
									 social_distance_strictness = social_distance_strictness[i],
									 restriction_decreasing = restriction_decreasing[i],
									 n_initial_infected_nodes = n_initial_infected_nodes[i],
									 R_0 = R_0[i],
									 n_test = n_test[i],
									 policy_test = policy_test[i],
									 contact_tracking_efficiency = contact_tracking_efficiency[i],
									 dump = False,
									 path = None,
									 seed = 42,
									 use_random_seed = True)

		network_history = compute_network_history(result_nets)

		list_nets_history.append(network_history)
		
		# to-do
		plot_network_info(result_nets, sim_name = name_list[i])
		
		plot_simulation(network_history, sim_name = name_list[i])
		
		if i == 0 or use_random_seed == False:
			# useless?
			print_degree_summary(result_nets[0], sim_name = name_list[i])

		

	
	#compare infected people in days
	plot_comparison_infected_dead(list_nets_history = list_nets_history, name_list = name_list , color_list = color_list)

	#pie chart at the end of simulation
	plot_pie_chart_summary(list_nets_history = list_nets_history, name_list = name_list)