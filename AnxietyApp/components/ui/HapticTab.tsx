import React from 'react';
import {
  TouchableOpacity,
  TouchableNativeFeedback,
  Platform,
  ViewStyle,
  StyleProp,
} from 'react-native';
import * as Haptics from 'expo-haptics';

type HapticTabProps = {
  onPress?: () => void;
  style?: StyleProp<ViewStyle>;
  children: React.ReactNode;
};

export function HapticTab({ onPress, style, children }: HapticTabProps) {
  const handlePress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onPress?.();
  };

  if (Platform.OS === 'android') {
    return (
      <TouchableNativeFeedback onPress={handlePress}>
        {children}
      </TouchableNativeFeedback>
    );
  }

  return (
    <TouchableOpacity onPress={handlePress} style={style}>
      {children}
    </TouchableOpacity>
  );
}