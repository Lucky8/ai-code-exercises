# performance_comparison.py
# Compare all optimized versions against the original

import time
import random
import sys

# Import all versions
import inventory_analysis as original
import inventory_analysis_v1_set_optimization as v1
import inventory_analysis_v2_two_pointer as v2
import inventory_analysis_v3_bucketing as v3

def run_benchmark(name, func, products, target_price, price_margin):
    """Run a function and measure its execution time"""
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        results = func(products, target_price, price_margin)
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"✓ Completed in {elapsed:.2f} seconds")
        print(f"  Found {len(results)} product combinations")
        return elapsed, len(results)
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, 0

if __name__ == "__main__":
    # Generate test data once (reuse across all versions)
    print("Generating Product List (5000 products)...")
    product_list = []
    for i in range(5000):
        product_list.append({
            'id': i,
            'name': f'Product {i}',
            'price': random.randint(5, 500)
        })
    
    target_price = 500
    price_margin = 50
    
    print(f"Dataset: {len(product_list)} products")
    print(f"Target: ${target_price} ± ${price_margin}")
    
    # Run benchmarks
    results = {}
    
    # Note: Original version might take 20-30 seconds, so we can skip it if you want
    # Uncomment the line below to include it:
    # results['Original (Slow)'] = run_benchmark('Original (O(n³) brute force)', original.find_product_combinations, product_list, target_price, price_margin)
    
    results['v1: Set Optimization'] = run_benchmark(
        'v1: Set Optimization (O(n²) with O(1) lookups)', 
        v1.find_product_combinations, 
        product_list, target_price, price_margin
    )
    
    results['v2: Two-Pointer'] = run_benchmark(
        'v2: Two-Pointer Algorithm (O(n²) optimized)', 
        v2.find_product_combinations, 
        product_list, target_price, price_margin
    )
    
    results['v3: Bucketing'] = run_benchmark(
        'v3: Bucketing by Price (O(n) with filtering)', 
        v3.find_product_combinations, 
        product_list, target_price, price_margin
    )
    
    # Print summary
    print(f"\n{'='*60}")
    print("PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    
    # Filter out None results (failed runs)
    valid_results = {k: v for k, v in results.items() if v[0] is not None}
    
    if not valid_results:
        print("No successful runs to compare")
        sys.exit(1)
    
    # Find baseline (slowest time)
    baseline_time = max(v[0] for v in valid_results.values())
    baseline_name = [k for k, v in valid_results.items() if v[0] == baseline_time][0]
    
    print(f"\nBaseline: {baseline_name} = {baseline_time:.2f}s\n")
    print(f"{'Method':<30} {'Time':<15} {'Speedup':<15} {'Results':<10}")
    print("-" * 70)
    
    for name, (elapsed, result_count) in sorted(valid_results.items(), key=lambda x: x[1][0]):
        speedup = baseline_time / elapsed
        print(f"{name:<30} {elapsed:>6.2f}s        {speedup:>6.1f}x         {result_count:>8}")
    
    print("\nNote: Higher speedup = better performance")
    print("\nRecommendation:")
    print("  - Start with v1 for easiest implementation")
    print("  - Use v2 for consistent, predictable performance")
    print("  - Use v3 when dealing with very large datasets")
