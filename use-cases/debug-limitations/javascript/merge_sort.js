function mergeSort(arr, compare = (a, b) => a - b) {
    if (!Array.isArray(arr)) {
        throw new TypeError("Expected an array");
    }

    if (arr.length <= 1) return [...arr];

    const mid = Math.floor(arr.length / 2);
    const left = mergeSort(arr.slice(0, mid), compare);
    const right = mergeSort(arr.slice(mid), compare);

    return merge(left, right, compare);
}

function merge(left, right, compare) {
    const result = [];
    let leftIndex = 0;
    let rightIndex = 0;

    while (leftIndex < left.length && rightIndex < right.length) {
        if (compare(left[leftIndex], right[rightIndex]) <= 0) {
            result.push(left[leftIndex]);
            leftIndex++;
        } else {
            result.push(right[rightIndex]);
            rightIndex++;
        }
    }

    return result
        .concat(left.slice(leftIndex))
        .concat(right.slice(rightIndex));
}

// Export functions for testing
module.exports = { mergeSort };
