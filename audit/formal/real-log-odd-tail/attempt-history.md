# The second stock Linux attempt

The second proof body used the original statement and frozen judge. The model compiled. At line 24 the proof tried to reverse a function from an equality to false. Only an equality has the symmetry operation used on that line. The compiler exited with status 1. Its diagnostic term used a placeholder axiom. This term supplies no proof. The fresh checker and the separate negative control never started.

The third registered body takes a hypothetical reversed equality, reverses that equality, and applies the recorded inequality to it. The earlier attempt and its original result remain available. [Original public execution](https://github.com/sepahead/pid-rs/actions/runs/45567721612).
