import React from 'react';
import { View, StyleSheet } from 'react-native';

interface ProgressBarProps {
  progress: number; // 0 to 1
  width?: number | null;
  height?: number;
  color?: string;
  unfilledColor?: string;
  borderWidth?: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  width = null,
  height = 6,
  color = '#2196f3',
  unfilledColor = '#e0e0e0',
  borderWidth = 0,
}) => {
  const clampedProgress = Math.min(Math.max(progress, 0), 1);
  
  return (
    <View
      style={[
        styles.container,
        {
          height,
          backgroundColor: unfilledColor,
          borderWidth,
          borderColor: color,
          width: width || '100%',
        },
      ]}
    >
      <View
        style={[
          styles.progress,
          {
            width: `${clampedProgress * 100}%`,
            backgroundColor: color,
            height: height - (borderWidth * 2),
          },
        ]}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 4,
    overflow: 'hidden',
  },
  progress: {
    borderRadius: 4,
  },
});

export default ProgressBar;
