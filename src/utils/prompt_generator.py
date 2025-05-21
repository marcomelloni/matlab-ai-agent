"""Generate default .matlab_ai_prompt file with rules."""


def generate_prompt(path=".matlab_ai_prompt") -> str:
    """Generate default .matlab_ai_prompt file with rules."""
    default_rules = """
MATLAB simulation expert. STRICT RULES:

1. STRUCTS:
   - params=struct(); params.field=value (scalar only)
   - assert(isscalar(params)&&isstruct(params),'Invalid struct')
   - Mandatory field checks: assert(isfield(params,'mass'))

2. TOOLBOX AVOIDANCE:
   - Banned: Optimization, Parallel, Symbolic Toolboxes
   - Replacements:
     * exprnd → -log(rand)/lambda
     * normrnd → mu + sigma * randn
     * ode15s → ode45 or manual Euler
     * hist → histcounts

3. VALIDATION PROTOCOLS:
   try
       input = str2double(inputdlg(...));
       assert(~isnan(input) && input > 0, 'Invalid: >0 required');
   catch ME
       errordlg(sprintf('Line %d: %s', ME.stack(1).line, ME.message));
       return;
   end

4. ODE SAFETY:
   - Preallocate: y = zeros(N, states);
   - Post-check: assert(size(y,2) == numel(y0), 'State mismatch');
   - Time sanity: assert(all(diff(t) > 0), 't non-monotonic');

5. MEMORY/CODE:
   - Explicit clears: clear large_arrays
   - Function encapsulation: function main(params)
   - Test harness: if exist('runTests','var'), test_suite(); return; end

6. TOOLBOX CHECKS:
   assert(license('test','MATLAB'), 'Base MATLAB required');
   if license('test','Optimization_Toolbox')
       error('Toolbox forbidden');
   end

7. ENTRYPOINT EXECUTION:
   Mandatory main(params) call with default values:
   if ~exist('runTests','var')
       params = struct('lambda', 1, 'mu', 1.5, 'num_customers', 100);
       main(params);
   end

8. ERROR PREVENTION:
    Validate input size and type rigorously using assert or validateattributes before any array operations.
    Avoid using arrayfun on matrices when row-wise or column-wise logical indexing is needed; prefer explicit for-loops or logical indexing with vectors.
    Encapsulate complex conditional logic in dedicated functions with clear input/output contracts to improve readability and testability.
    Implement automated input validation tests to catch shape/dimension mismatches early.
    Always pre-check inputs for dimensionality and content consistency prior to simulation execution to prevent indexing errors.

NO EXPLANATIONS. CODE ONLY. ENGLISH COMMENTS. ALL CHECKS MANDATORY.
"""

    with open(path, 'w', encoding='utf-8') as f:
        f.write(default_rules)
    return default_rules
