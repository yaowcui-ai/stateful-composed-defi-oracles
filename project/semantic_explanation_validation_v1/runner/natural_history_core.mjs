export function adjacentWindows(anchorTimestamp, days=7) {
  const width = days * 24 * 60 * 60;
  return [
    {id:"W1", startTimestamp:anchorTimestamp-2*width, endTimestamp:anchorTimestamp-width-1},
    {id:"W2", startTimestamp:anchorTimestamp-width, endTimestamp:anchorTimestamp-1},
  ];
}

export function deterministicSample(items, maximum=200) {
  if (items.length <= maximum) return items;
  const stride = items.length / maximum;
  return Array.from({length:maximum}, (_,i) => items[Math.floor(i*stride)]);
}
