import React from 'react';
import { Ionicons } from '@expo/vector-icons';

type IconSymbolProps = {
  name: React.ComponentProps<typeof Ionicons>['name'];
  size: number;
  color: string;
};

export function IconSymbol({ name, size, color }: IconSymbolProps) {
  return <Ionicons name={name} size={size} color={color} />;
}