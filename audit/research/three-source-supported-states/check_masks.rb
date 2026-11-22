# Finite controls using integer-valued Boolean functions on the 16 joint states.
require 'json'

def check(value, label)
  raise ArgumentError, label unless value
end

def branches(family)
  (0...8).select { |mask| family[mask] == 1 }
end

def event(family, matches)
  branches(family).any? { |mask| mask & matches == mask }
end

def pair(q)
  [q.numerator, q.denominator]
end

valid = (0...256).select do |f|
  masks = branches(f)
  !masks.empty? && !masks.include?(0) &&
    masks.combination(2).all? { |a,b| (a & b) != a && (a & b) != b }
end
check(valid.size == 18, 'carrier')
truth = [0,0,0,0]
(0...256).each do |f|
  (0...8).each do |agreements|
    [0,1].each do |target_equal|
      external = target_equal == 1 && event(f, agreements)
      keep_coordinates = target_equal == 1 ? 7 : 0
      distributed = event(f, agreements & keep_coordinates)
      difference = (distributed ? 1 : 0) - (external ? 1 : 0)
      check(difference == (f[0] == 1 && target_equal == 0 ? 1 : 0), 'distributive formula')
      truth[0] += 1
      truth[1] += difference
      if valid.include?(f)
        truth[2] += 1
        truth[3] += difference
      end
    end
  end
end

# A region is an integer with one set bit for each world in a predicate.
worlds = (0...16).to_a
regions = {}
valid.concat([1]).each do |f|
  worlds.each do |key|
    e = worlds.sum { |world| event(f, 7 ^ ((world ^ key) & 7)) ? (1 << world) : 0 }
    g = worlds.sum { |world| world[3] == key[3] ? (1 << world) : 0 }
    regions[[f,key]] = [65535, e, e & g, g]
  end
end
valid.delete(1)

def mass(table, region)
  table.sum { |world,weight| weight * region[world] }
end

counts = lambda do |table,key,family|
  regions.fetch([family,key]).map { |region| mass(table,region) }
end
all_sources = 1 << 7
x_source = 1 << 1
y_source = 1 << 2
both_singletons = x_source | y_source
laws = [[]]
worlds.each { |a| [1,2].each { |k| laws << [[a,k]] } }
worlds.combination(2) do |a,b|
  [1,2].repeated_permutation(2) { |i,j| laws << [[a,i],[b,j]] }
end
support = [laws.size,0,0,0]
laws.each do |table|
  worlds.each do |reference|
    c = mass(table, 1 << reference)
    js = valid.map { |f| mass(table, regions.fetch([f,reference])[2]) }
    top = mass(table, regions.fetch([all_sources,reference])[2])
    check(top == c && js.min == c && js.all?(&:positive?) == c.positive?, 'all-node support')
    support[1] += 1
    support[2] += js.size
    support[3] += 1 if c.positive?
  end
end

empty_case = [[0,1],[13,1]]
outside = counts.call(empty_case,0,1)[2]
# With a target mismatch the bitwise coordinate filter deletes every source match.
# Evaluate the empty-branch family after applying that filter.
distributed_region = worlds.sum do |j|
  possible = j[3].zero? ? ((~j) & 7) : 0
  event(1,possible) ? (1 << j) : 0
end
inside = mass(empty_case,distributed_region)
duplicate_case = [[0,2],[0,3],[15,1],[0,0]]
min_at = lambda { |key| valid.map { |f| counts.call(duplicate_case,key,f)[2] }.min }
zero_member = duplicate_case.last.first
outside_copy = 0
one_node = [x_source,all_sources].map { |f| counts.call([[0,1]],4,f) }

# Encode the four states separately from the Python product generator.
# S1, S2, S3, T occupy the 1, 2, 4 and 8 bits, respectively.
signed_table = [[0,1],[14,1],[5,1],[11,1]]
signed = [both_singletons,x_source,y_source].map do |f|
  values = signed_table.map { |j,_| counts.call(signed_table,j,f) }
  check(values.uniq.size == 1,'translation over the four parity-coded states')
  n,u,v,t = values.first
  net = Rational(v,u) / Rational(t,n)
  plus = Rational(1,1) / Rational(u,n)
  minus = Rational(1,1) / Rational(v,t)
  check(net == plus/minus,'conditional ratio')
  product = values.zip(signed_table).reduce(1.to_r) do |q,(observed,entry)|
    n0,u0,v0,t0 = observed
    q * (Rational(v0,u0)/Rational(t0,n0))**entry.last
  end
  {counts: values.first, plus: pair(plus), minus: pair(minus), net: pair(net), net_product: pair(product)}
end
# Read the copy as three unit observations here, including two identical worlds.
expanded = [[0,1],[0,1],[15,1]]
per_observation = expanded.map do |j,_|
  n,u,v,t = counts.call(expanded,j,all_sources)
  Rational(v,u)/Rational(t,n)
end
expanded_product = per_observation.reduce(:*)
by_distinct_key = per_observation.uniq.reduce(:*)
answer = {truth: truth, support: support,
          fixtures: {empty_branch_joint_counts: [outside,inside],
                     duplicate_and_outside_minima: [min_at.call(zero_member),min_at.call(outside_copy)],
                     absent_singleton_and_top: one_node, signed: signed,
                     weighted_copy_products: [pair(expanded_product),pair(by_distinct_key)]}}
check(truth == [4096,1024,288,0], 'fixed truth domain')
check(support == [513,8208,147744,992], 'fixed support domain')
check([outside,inside] == [1,2] && one_node == [[1,1,1,1],[1,0,0,1]], 'boundary examples')
check([expanded_product,by_distinct_key] == [Rational(27,4),Rational(9,2)], 'weighting')
check(signed.map { |r| r[:net] } == [[4,3],[1,1],[2,1]], 'two comparable pairs')
puts JSON.generate(answer)
