# Contractor Processing System - Testing Guide

## Overview

This guide provides comprehensive testing procedures for the contractor processing system, including batch testing, validation, and analysis.

## Quick Start

### Single Command for 100-Contractor Test

```bash
docker-compose exec app python scripts/run_comprehensive_test.py --limit 100 --show-details
```

This command will:
- Process 100 contractors
- Display detailed results table
- Show comprehensive analysis
- Provide quality assessment

## Available Test Commands

### 1. Quick Test (10 contractors)
```bash
docker-compose exec app python scripts/run_comprehensive_test.py --limit 10
```

### 2. Comprehensive Test (100 contractors)
```bash
docker-compose exec app python scripts/run_comprehensive_test.py --limit 100 --show-details
```

### 3. Test Specific Problematic Cases
```bash
docker-compose exec app python scripts/run_comprehensive_test.py --test-specific
```

### 4. Show Help
```bash
docker-compose exec app python scripts/run_comprehensive_test.py --help
```

## Test Features

### ✅ What the Test Suite Provides

1. **Batch Processing**: Process multiple contractors efficiently
2. **Real-time Progress**: See processing status for each contractor
3. **Comprehensive Analysis**: 
   - Website discovery rate
   - Confidence distribution
   - Category distribution
   - Home contractor identification
   - Error rate analysis
4. **Quality Assessment**: Automatic grading of system performance
5. **Detailed Results**: Optional detailed table with all results
6. **Specific Case Testing**: Validate system improvements

### 📊 Metrics Tracked

- **Website Discovery Rate**: Percentage of contractors with websites found
- **Confidence Distribution**: High (≥0.8), Medium (0.6-0.79), Low (<0.6)
- **Home Contractor Rate**: Percentage identified as home contractors
- **Category Distribution**: Breakdown by service category
- **Error Rate**: Processing errors and failures
- **Processing Time**: Total time for batch processing

### 🎯 Quality Benchmarks

| Metric | Excellent | Good | Fair | Poor |
|--------|-----------|------|------|------|
| Website Discovery | ≥80% | ≥60% | ≥40% | <40% |
| High Confidence | ≥30% | ≥20% | ≥10% | <10% |
| Error Rate | ≤5% | ≤10% | ≤20% | >20% |

## Understanding Results

### Confidence Scores
- **0.8-1.0**: High confidence - likely correct match
- **0.6-0.79**: Medium confidence - probably correct
- **0.4-0.59**: Low confidence - questionable match
- **<0.4**: Very low confidence - likely incorrect

### Review Status
- **approved_download**: High-quality result ready for export
- **pending_review**: Needs manual review
- **rejected**: Failed validation
- **unknown**: Not yet reviewed

### Home Contractor
- **Yes**: Identified as residential contractor
- **No**: Commercial or unclear focus

## Recent System Improvements

### ✅ Strict Validation Implemented

The system now uses **strict validation** to prevent incorrect matches:

1. **Business Name Matching**: Must have strong business name match
2. **Geographic Validation**: Must have WA location indicators
3. **Domain Validation**: Business name should be in domain
4. **Directory Filtering**: Rejects directory/association sites
5. **Higher Threshold**: Requires 0.4+ confidence for acceptance

### 🎯 Problem Cases Fixed

Previously problematic cases are now correctly handled:

| Case | Previous Result | Current Result | Status |
|------|----------------|----------------|---------|
| 509 HEATING & COOLING → thermallheating.com | ❌ Accepted | ✅ Rejected | Fixed |
| 509 SERVICES → nevinfloorcompany.com | ❌ Accepted | ✅ Rejected | Fixed |
| 57 Wood Floors → straitfloors.com | ❌ Accepted | ✅ Rejected | Fixed |
| 5 Star Guttering → 5starguttering.com | ✅ Accepted | ✅ Accepted | Working |

## Troubleshooting

### Common Issues

1. **No Pending Contractors**: All contractors already processed
   - Solution: Reset contractor status or import new data

2. **Low Website Discovery**: System being too strict
   - Solution: Review confidence thresholds

3. **High Error Rate**: System issues
   - Solution: Check logs and API configurations

### Performance Tips

1. **Start Small**: Use `--limit 10` for quick tests
2. **Monitor Progress**: Watch real-time processing output
3. **Check Quality**: Review confidence distribution
4. **Validate Results**: Spot-check high-confidence results

## Script Files

### Main Testing Scripts
- `scripts/run_comprehensive_test.py` - Main testing suite
- `scripts/test_contractor_batch.py` - Legacy batch testing
- `scripts/show_recent_results.py` - View recent results

### Validation Scripts
- `scripts/test_strict_validation.py` - Test validation logic
- `scripts/test_legitimate_case.py` - Test legitimate cases
- `scripts/debug_specific_cases.py` - Debug specific issues

### Analysis Scripts
- `scripts/clean_results_table.py` - Display clean results
- `scripts/extract_results.py` - Extract processed results

## Best Practices

1. **Regular Testing**: Run tests after system changes
2. **Monitor Quality**: Track confidence and discovery rates
3. **Validate Improvements**: Test specific cases after fixes
4. **Document Issues**: Note any problematic patterns
5. **Iterate**: Use results to guide system improvements

## Example Workflow

```bash
# 1. Quick validation test
docker-compose exec app python scripts/run_comprehensive_test.py --test-specific

# 2. Small batch test
docker-compose exec app python scripts/run_comprehensive_test.py --limit 10

# 3. Comprehensive test
docker-compose exec app python scripts/run_comprehensive_test.py --limit 100 --show-details

# 4. Review results and iterate
```

This testing framework provides comprehensive validation of the contractor processing system with clear metrics and actionable insights. 