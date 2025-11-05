export function getPercentsFromWeights(weights: number[]): number[] {
    const cleaned = weights.map(w => (Number.isFinite(w) && w > 0 ? w : 0));
    const total = cleaned.reduce((a, b) => a + b, 0);
    if (total === 0)// zero total mass
    {
        if (cleaned.length === 0) return []; // no weights at all, return empty array
        const even = Math.round(100 / cleaned.length);
        // distribute evenly across all categories
        const base = Array(cleaned.length).fill(even);
        // fix rounding
        let diff = 100 - base.reduce((a, b) => a + b, 0);
        for (let i = 0; i < base.length && diff !== 0; i++) {
            base[i] += diff > 0 ? 1 : -1;
            diff += diff > 0 ? -1 : 1;
        }
        return base;
    }

    // divide each weight by total mass and round to exact percent
    const roundedVals = cleaned.map(w => Math.round((w / total) * 100));
    return roundedVals
}