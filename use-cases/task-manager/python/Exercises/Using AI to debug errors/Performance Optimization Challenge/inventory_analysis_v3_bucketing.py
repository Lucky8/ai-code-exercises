# inventory_analysis_v3_bucketing.py
# OPTIMIZATION 3: Bucketing by Price Range
# Instead of comparing all pairs, only compare products in relevant price ranges
# Group products by price, then only look at nearby groups

def find_product_combinations(products, target_price, price_margin=10):
    """
    Find all pairs of products where the combined price is within
    the target_price ± price_margin range.
    
    OPTIMIZATION: Price Bucketing
    - Group products into price buckets (e.g., $0-$10, $10-$20, etc.)
    - For each product, calculate which bucket the complementary price is in
    - Only compare against products in that bucket (and nearby buckets)
    - Dramatically reduces number of comparisons
    
    Args:
        products: List of dictionaries with 'id', 'name', and 'price' keys
        target_price: The ideal combined price
        price_margin: Acceptable deviation from the target price

    Returns:
        List of dictionaries with product pairs and their combined price
    """
    from collections import defaultdict
    
    # Bucket size - tuning this affects performance
    BUCKET_SIZE = 20  # Group products in $20 ranges
    
    # Group products by price bucket (O(n))
    price_buckets = defaultdict(list)
    for product in products:
        bucket = product['price'] // BUCKET_SIZE
        price_buckets[bucket].append(product)
    
    results = []
    seen_pairs = set()
    
    print(f"Created {len(price_buckets)} price buckets")
    
    # For each product, find complementary products
    for idx, product1 in enumerate(products):
        if idx % 100 == 0:
            print(f"Processing product {idx+1} of {len(products)}")
        
        # Calculate what price we need to hit target
        needed_price = target_price - product1['price']
        needed_bucket = needed_price // BUCKET_SIZE
        
        # Only check buckets that could contain valid pairs
        # Check the target bucket and one bucket on each side
        buckets_to_check = [needed_bucket - 1, needed_bucket, needed_bucket + 1]
        
        comparisons = 0
        for bucket_offset in buckets_to_check:
            if bucket_offset in price_buckets:
                for product2 in price_buckets[bucket_offset]:
                    comparisons += 1
                    
                    # Skip comparing product with itself
                    if product1['id'] == product2['id']:
                        continue
                    
                    combined_price = product1['price'] + product2['price']
                    
                    # Check if within range
                    if (target_price - price_margin) <= combined_price <= (target_price + price_margin):
                        # Avoid duplicates using set
                        pair_key = tuple(sorted([product1['id'], product2['id']]))
                        if pair_key not in seen_pairs:
                            seen_pairs.add(pair_key)
                            pair = {
                                'product1': product1,
                                'product2': product2,
                                'combined_price': combined_price,
                                'price_difference': abs(target_price - combined_price)
                            }
                            results.append(pair)
    
    # Sort by price difference from target
    results.sort(key=lambda x: x['price_difference'])
    return results

# Example usage
if __name__ == "__main__":
    import time
    import random

    # Generate a large list of products
    print("Generating Product List")
    product_list = []
    for i in range(5000):
        product_list.append({
            'id': i,
            'name': f'Product {i}',
            'price': random.randint(5, 500)
        })

    # Measure execution time
    print(f"Finding product combinations for {len(product_list)} products")
    start_time = time.time()
    combinations = find_product_combinations(product_list, 500, 50)
    end_time = time.time()

    print(f"Found {len(combinations)} product combinations")
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    print(f"\nTop 5 best matches:")
    for i, combo in enumerate(combinations[:5]):
        print(f"  {i+1}. {combo['product1']['name']} (${combo['product1']['price']}) + {combo['product2']['name']} (${combo['product2']['price']}) = ${combo['combined_price']}")
