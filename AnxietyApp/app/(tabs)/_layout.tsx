// app/(tabs)/_layout.tsx

import React from 'react';
import { Tabs } from 'expo-router';
import { Platform } from 'react-native';

import { HapticTab } from '../../components/ui/HapticTab';
import { IconSymbol } from '../../components/ui/IconSymbol';
import TabBarBackground from '../../components/ui/TabBarBackground';
// import { Colors } from '../../constants/Colors';
import { Colors } from '../../constants/Colors';
import { useColorScheme } from '../../hooks/useColorScheme';

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarButton: (props) => (
          <HapticTab
            {...props}
            onPress={
              props.onPress
                ? () => (props.onPress as (e: any) => void)?.({})
                : undefined
            }
          />
        ),  // render-prop
        tabBarBackground: () => <TabBarBackground />,       // render-prop
        tabBarActiveTintColor: Colors[colorScheme ?? 'light'].tint,
        tabBarInactiveTintColor: 'gray',
        tabBarShowLabel: false,
        tabBarHideOnKeyboard: true,
        tabBarStyle: {
          height: Platform.select({ web: 72, default: 70 }),
        },
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="home" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Explore',
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="paper-plane" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="person" color={color} />
          ),
        }}
      />
    </Tabs>
  );
}