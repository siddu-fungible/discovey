num_redip = 3
original_values = [16,11,7,4,1]
values = original_values
probs = [1.0/len(values)]*len(values)

expected_value = 0
for sub_index in range(len(probs)):
		expected_value += probs[sub_index] * values[sub_index]

print(expected_value)

for index in range(num_redip):
	new_values = []
	new_probs = []
	for sub_index in range(len(values)):
		if values[sub_index] < expected_value:
			new_values.extend(original_values)
			new_probs.extend([probs[sub_index]/len(original_values) for _ in range(len(original_values))])
		else:
			new_values.append(values[sub_index])
			new_probs.append(probs[sub_index])

	values = new_values
	probs = new_probs

	new_expected_value = 0

	for sub_index in range(len(values)):
		new_expected_value += values[sub_index] * probs[sub_index]


	expected_value = new_expected_value
	print(expected_value)